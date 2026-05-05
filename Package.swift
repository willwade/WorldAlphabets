// swift-tools-version: 5.5
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "WorldAlphabets",
    products: [
        // Products define the executables and libraries a package produces, making them visible to other packages.
        .library(
            name: "WorldAlphabets",
            targets: ["WorldAlphabets"]),
    ],
    targets: [
        // Targets are the basic building blocks of a package, defining a module or a test suite.
        // Targets can depend on other targets in this package and products from dependencies.
        .target(
            name: "WorldAlphabetsC",
            path: "c",
            exclude: [
                "CMakeLists.txt",
                "tests"
            ],
            sources: [
                "src",
                "generated"
            ],
            publicHeadersPath: "include"
        ),
        .target(
            name: "WorldAlphabets",
            dependencies: ["WorldAlphabetsC"],
            path: "swift/Sources/WorldAlphabets"
        ),
        .testTarget(
            name: "WorldAlphabetsTests",
            dependencies: ["WorldAlphabets"],
            path: "swift/Tests/WorldAlphabetsTests"
        ),
    ]
)
