import SwiftUI
import CoreText
#if os(macOS)
import AppKit
#else
import UIKit
#endif

/// Same palette as the Android Material theme: primary = verse numbers/accents, tertiary = bookmarked verses.
enum Theme {
    static let primary = Color(light: 0x6650A4, dark: 0xD0BCFF)
    static let tertiary = Color(light: 0x7D5260, dark: 0xEFB8C8)
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255)
    }

    init(light: UInt32, dark: UInt32) {
        #if os(macOS)
        self.init(nsColor: NSColor(name: nil) { appearance in
            NSColor(Color(hex: appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua ? dark : light))
        })
        #else
        self.init(uiColor: UIColor { traits in
            UIColor(Color(hex: traits.userInterfaceStyle == .dark ? dark : light))
        })
        #endif
    }
}

/// Reader font choices offered in Settings; key is what gets persisted.
let fontChoices: [(key: String, name: String)] = [
    ("literata", "Literata"), ("serif", "Serif"), ("sans", "Sans"), ("mono", "Mono"),
]

func readerFont(_ key: String, size: CGFloat) -> Font {
    switch key {
    case "literata": .custom("Literata", size: size)
    case "serif": .system(size: size, design: .serif)
    case "mono": .system(size: size, design: .monospaced)
    default: .system(size: size)
    }
}

/// Literata ships inside the resources bundle, so register it at runtime instead of via Info.plist.
func registerFonts() {
    guard let url = resourceURL("Literata.ttf") else { return }
    CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil)
}
