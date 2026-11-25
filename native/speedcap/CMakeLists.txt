# speedcap - a RED4ext plugin that lifts the 100 m/s vehicle speed wall.
#
# Needs the RED4ext SDK as a sibling checkout (examples/ in the SDK use the same pattern):
#
#   git clone https://github.com/WopsS/RED4ext.SDK.git native/deps/red4ext.sdk
#   cmake -S native/speedcap -B native/speedcap/build -G "Visual Studio 17 2022" -A x64 ^
#         -DRED4EXT_SDK_DIR=<abs path>/native/deps/red4ext.sdk
#   cmake --build native/speedcap/build --config Release
#
# The DLL lands in build/Release/speedcap.dll -> red4ext\plugins\speedcap\speedcap.dll

cmake_minimum_required(VERSION 3.20)
project(speedcap LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT RED4EXT_SDK_DIR)
  set(RED4EXT_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../deps/red4ext.sdk")
endif()

if(NOT EXISTS "${RED4EXT_SDK_DIR}/CMakeLists.txt")
  message(FATAL_ERROR "RED4ext SDK not found at ${RED4EXT_SDK_DIR}; set -DRED4EXT_SDK_DIR=...")
endif()

add_subdirectory(${RED4EXT_SDK_DIR} "${CMAKE_CURRENT_BINARY_DIR}/red4ext.sdk")

add_library(speedcap SHARED main.cpp)
target_link_libraries(speedcap PRIVATE RED4ext::SDK)
target_compile_definitions(speedcap PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
set_target_properties(speedcap PROPERTIES PREFIX "" OUTPUT_NAME "speedcap")
