add_library(usermod_can INTERFACE)

target_sources(usermod_can INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modcan.c
)

target_include_directories(usermod_can INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_can)
