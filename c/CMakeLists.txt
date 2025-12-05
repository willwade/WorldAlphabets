cmake_minimum_required(VERSION 3.15)
project(worldalphabets C)

add_library(worldalphabets STATIC
    src/worldalphabets.c
    generated/worldalphabets_data.c
)

add_library(worldalphabets_shared SHARED
    src/worldalphabets.c
    generated/worldalphabets_data.c
)
set_target_properties(worldalphabets_shared PROPERTIES OUTPUT_NAME worldalphabets)
target_include_directories(worldalphabets_shared PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

target_include_directories(worldalphabets PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(worldalphabets PUBLIC c_std_99)
target_link_libraries(worldalphabets PUBLIC m)
target_link_libraries(worldalphabets_shared PUBLIC m)

install(TARGETS worldalphabets
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

enable_testing()
add_executable(wa_smoke tests/smoke.c)
target_link_libraries(wa_smoke worldalphabets)
add_test(NAME wa_smoke COMMAND wa_smoke)
