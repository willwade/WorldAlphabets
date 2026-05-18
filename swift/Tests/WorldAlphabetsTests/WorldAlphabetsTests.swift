import XCTest
@testable import WorldAlphabets

final class WorldAlphabetsTests: XCTestCase {

    func testGetAvailableCodes() {
        let codes = WorldAlphabets.getAvailableCodes()
        XCTAssertFalse(codes.isEmpty, "Should have available codes")
        XCTAssertTrue(codes.contains("en"), "Should contain English code")
        XCTAssertTrue(codes.contains("ja"), "Should contain Japanese code")
    }

    func testGetScripts() {
        let scripts = WorldAlphabets.getScripts(for: "ja")
        XCTAssertFalse(scripts.isEmpty, "Japanese should have scripts")
        XCTAssertTrue(scripts.contains("Jpan"), "Should contain Jpan script for Japanese")
    }

    func testLoadAlphabet() {
        let alphabet = WorldAlphabets.loadAlphabet(code: "en")
        XCTAssertNotNil(alphabet, "English alphabet should load")
        if let alphabet = alphabet {
            XCTAssertEqual(alphabet.language, "en")
            XCTAssertTrue(alphabet.lowercase.contains("a"))
            XCTAssertTrue(alphabet.uppercase.contains("Z"))
            XCTAssertTrue(alphabet.digits.contains("0"))
        }
    }

    func testDetectLanguages() {
        let text = "This is a simple test in English"
        let results = WorldAlphabets.detectLanguages(text: text)
        XCTAssertFalse(results.isEmpty, "Should detect a language")

        let firstLang = results.first?.language
        XCTAssertEqual(firstLang, "en", "First detected language should be English")
    }

    func testKeyboards() {
        let layouts = WorldAlphabets.getAvailableLayouts()
        XCTAssertFalse(layouts.isEmpty, "Should have keyboard layouts available")

        if let firstId = layouts.first {
            let layout = WorldAlphabets.loadKeyboard(layoutId: firstId)
            XCTAssertNotNil(layout, "Should load keyboard layout")
            XCTAssertEqual(layout?.id, firstId)
            XCTAssertFalse(layout?.layers.isEmpty ?? true, "Layout should have layers")
        }
    }

    func testFindLayoutsByHid() {
        // HID Usage 0x04 is 'A' key on US layout
        let matches = WorldAlphabets.findLayoutsByHid(hidUsage: 0x04, layerName: "default")
        XCTAssertFalse(matches.isEmpty, "Should find layout mappings for HID 0x04")
    }
}
