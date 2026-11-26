// speedcap - lift the game's vehicle speed wall (100 m/s = 360 km/h = 223 mph)
//
// WHAT THIS DOES, AND WHY IT IS SHAPED THIS WAY
//
// The game throws away the frame's velocity when `vehicle::RigidBody::Recalculate` returns a
// non-finite result, and it does that at exactly 100 m/s. The car keeps the velocity it had, which
// is the "invisible wall" every fast-car mod hits. No TweakXL or redscript value can reach it,
// because both run above this function.
//
// So this plugin does what Vehicle Speed Unlimiter 1.0.2 does - recompute the velocity from the
// force and write it back over what the engine refused - with one deliberate difference:
//
//   Vehicle Speed Unlimiter uses RED4ext::UniversalRelocBase::Resolve(), which CALLS
//   ShowErrorAndTerminateProcess() when a hash is missing. That is why it stops the game from
//   loading on 2.5: an outdated hash is a message box and an exit, not a disabled mod.
//
// This one calls RED4ext_ResolveAddress() directly and gives up quietly if the hash is not in the
// installed RED4ext's address database. Worst case the mod does nothing; the game still starts.
//
// Addresses come from RED4ext's own database (x64\cyberpunk2077_addresses.json), so nothing here
// is patch-specific and nothing needs recompiling when the game updates - as long as the hashes
// are in that file. Check with:
//
//   findstr /C:"593628708" /C:"4067628720" "x64\cyberpunk2077_addresses.json"
//
// Hashes (from jackhumbert/let_there_be_flight, MIT, src/red4ext/Physics/VehicleSpeedUnlimiter.cpp):
//   593628708   vehicle::RigidBody::Recalculate(vehicle::PhysicsData*) -> short
//   4067628720  vehicle::RigidBody::ForceSetLinearVelocity(vehicle::PhysicsData*, Vector3*)
//
// NOT TESTED IN GAME. Treat as experimental, back up the save, and remove the DLL by deleting
// red4ext\plugins\speedcap.

#include <RED4ext/RED4ext.hpp>

#include <Windows.h>
#include <float.h>
#include <cstdint>

namespace {

// Hashes, as used by a mod that works on the current patch.
constexpr uint32_t HashRigidBodyRecalculate = 593628708u;
constexpr uint32_t HashForceSetLinearVelocity = 4067628720u;

// The first 0x34 bytes of vehicle::PhysicsData, which is all this needs.
// Layout from RED4ext.SDK (jackhumbert fork, include/RED4ext/Scripting/Natives/vehiclePhysicsData.hpp):
//   Vector3 force            0x00
//   Vector3 torque           0x0C
//   Vector3 velocity         0x18
//   Vector3 angularVelocity  0x24
//   float   inverseMass      0x30
struct PhysicsData
{
    float force[3];
    float torque[3];
    float velocity[3];
    float angularVelocity[3];
    float inverseMass;
};
static_assert(sizeof(PhysicsData) == 0x34, "PhysicsData prefix must be 0x34 bytes");
static_assert(offsetof(PhysicsData, velocity) == 0x18, "velocity offset");
static_assert(offsetof(PhysicsData, inverseMass) == 0x30, "inverseMass offset");

using Recalculate_t = short(__fastcall*)(PhysicsData*);
using ForceSetLinearVelocity_t = short(__fastcall*)(PhysicsData*, float* /* Vector3 */);

Recalculate_t Recalculate_Original = nullptr;
ForceSetLinearVelocity_t ForceSetLinearVelocity_Original = nullptr;

// The whole point. The original decides the frame's velocity from force, and returns
// FP_INFINITE when it refuses; we keep its return value (callers depend on it) but restore a
// velocity that was actually integrated.
short __fastcall Recalculate_Hook(PhysicsData* aPhysics)
{
    const float fx = aPhysics->force[0] * aPhysics->inverseMass;
    const float fy = aPhysics->force[1] * aPhysics->inverseMass;
    const float fz = aPhysics->force[2] * aPhysics->inverseMass;

    const auto result = Recalculate_Original(aPhysics);

    if (result != FP_INFINITE)
    {
        aPhysics->velocity[0] += fx;
        aPhysics->velocity[1] += fy;
        aPhysics->velocity[2] += fz;
    }

    return result;
}

// The game can also set the velocity directly (summoning, respawn, autopilot). Those writes must
// survive the same refusal, or the car snaps back to the wall.
short __fastcall ForceSetLinearVelocity_Hook(PhysicsData* aPhysics, float* aVelocity)
{
    const auto result = ForceSetLinearVelocity_Original(aPhysics, aVelocity);

    if (result != FP_INFINITE && aVelocity)
    {
        aPhysics->velocity[0] = aVelocity[0];
        aPhysics->velocity[1] = aVelocity[1];
        aPhysics->velocity[2] = aVelocity[2];
    }

    return result;
}

using ResolveAddress_t = uintptr_t(__stdcall*)(uint32_t);

ResolveAddress_t GetResolver()
{
    static ResolveAddress_t resolver = []() -> ResolveAddress_t {
        const auto module = GetModuleHandleW(L"RED4ext.dll");
        if (!module)
        {
            return nullptr;
        }
        return reinterpret_cast<ResolveAddress_t>(GetProcAddress(module, "RED4ext_ResolveAddress"));
    }();
    return resolver;
}

// Resolve without dying: UniversalRelocBase::Resolve() shows a message box and exits the process
// on a miss, which is exactly how the 2025 unlimiter breaks the game.
uintptr_t ResolveQuietly(uint32_t aHash)
{
    const auto resolver = GetResolver();
    return resolver ? resolver(aHash) : 0;
}

} // namespace

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::PluginHandle aHandle, RED4ext::v1::EMainReason aReason,
                                        const RED4ext::v1::Sdk* aSdk)
{
    switch (aReason)
    {
    case RED4ext::v1::EMainReason::Load:
    {
        const auto recalculate = ResolveQuietly(HashRigidBodyRecalculate);
        if (!recalculate)
        {
            aSdk->logger->ErrorF(aHandle,
                                 "speedcap: hash %u is not in cyberpunk2077_addresses.json - not hooking. "
                                 "Update RED4ext; the game is unchanged.",
                                 HashRigidBodyRecalculate);
            return true;
        }

        const auto attached = aSdk->hooking->Attach(aHandle, reinterpret_cast<void*>(recalculate),
                                                    reinterpret_cast<void*>(&Recalculate_Hook),
                                                    reinterpret_cast<void**>(&Recalculate_Original));
        aSdk->logger->InfoF(aHandle, "speedcap: Recalculate at 0x%llX, attached=%d, original=0x%llX",
                            static_cast<unsigned long long>(recalculate), attached ? 1 : 0,
                            static_cast<unsigned long long>(reinterpret_cast<uintptr_t>(Recalculate_Original)));
        if (!attached)
        {
            return true; // the wall stays; the game runs
        }

        const auto forceSet = ResolveQuietly(HashForceSetLinearVelocity);
        if (forceSet)
        {
            const auto alsoAttached = aSdk->hooking->Attach(
                aHandle, reinterpret_cast<void*>(forceSet), reinterpret_cast<void*>(&ForceSetLinearVelocity_Hook),
                reinterpret_cast<void**>(&ForceSetLinearVelocity_Original));
            aSdk->logger->InfoF(aHandle, "speedcap: ForceSetLinearVelocity at 0x%llX, attached=%d",
                                static_cast<unsigned long long>(forceSet), alsoAttached ? 1 : 0);
        }
        else
        {
            aSdk->logger->WarnF(aHandle, "speedcap: hash %u missing - direct velocity writes not covered",
                                HashForceSetLinearVelocity);
        }

        break;
    }
    case RED4ext::v1::EMainReason::Unload:
    {
        const auto recalculate = ResolveQuietly(HashRigidBodyRecalculate);
        if (recalculate)
        {
            aSdk->hooking->Detach(aHandle, reinterpret_cast<void*>(recalculate));
        }
        const auto forceSet = ResolveQuietly(HashForceSetLinearVelocity);
        if (forceSet)
        {
            aSdk->hooking->Detach(aHandle, reinterpret_cast<void*>(forceSet));
        }
        break;
    }
    }

    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* aInfo)
{
    aInfo->name = L"speedcap";
    aInfo->author = L"phoenix_aston_cheats";
    aInfo->version = RED4EXT_V1_SEMVER(0, 1, 0);
    aInfo->runtime = RED4EXT_V1_RUNTIME_VERSION_LATEST;
    aInfo->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}
