// swift-tools-version: 6.0
import PackageDescription

// xtool builds the single library product below as the iOS app.
let package = Package(
    name: "GOIBible",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "GOIBible", targets: ["GOIBible"]),
    ],
    targets: [
        .target(
            name: "GOIBible",
            resources: [.copy("Resources")]
        ),
    ],
    swiftLanguageModes: [.v5]
)
