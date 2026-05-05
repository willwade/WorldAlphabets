import Foundation
import WorldAlphabetsC

/// Helper to convert a C string array (`wa_string_array`) to a Swift `[String]`.
private func stringArrayFromC(_ cArray: wa_string_array) -> [String] {
    var result: [String] = []
    if cArray.len > 0, let items = cArray.items {
        for i in 0..<Int(cArray.len) {
            if let cString = items[i] {
                result.append(String(cString: cString))
            }
        }
    }
    return result
}

public struct Alphabet {
    public let language: String
    public let script: String
    public let uppercase: [String]
    public let lowercase: [String]
    public let digits: [String]
    public let frequency: [String: Double]
}

public struct FrequencyList {
    public let language: String
    public let mode: String
    public let tokens: [String]
}

public struct DetectResult {
    public let language: String
    public let score: Double
}

public struct KeyboardMapping {
    public let keycode: UInt16
    public let value: String
}

public struct KeyboardLayer {
    public let name: String
    public let entries: [KeyboardMapping]
}

public struct KeyboardLayout {
    public let id: String
    public let name: String
    public let layers: [KeyboardLayer]
}

public struct LayoutMatch {
    public let layout: KeyboardLayout
    public let layer: KeyboardLayer
    public let mapping: KeyboardMapping
}

public struct WorldAlphabets {

    /// Get a list of available language codes
    public static func getAvailableCodes() -> [String] {
        return stringArrayFromC(wa_get_available_codes())
    }

    /// Get available scripts for a given language code
    public static func getScripts(for code: String) -> [String] {
        return code.withCString { cString in
            return stringArrayFromC(wa_get_scripts(cString))
        }
    }

    /// Load alphabet data for a given language code and optional script
    public static func loadAlphabet(code: String, script: String? = nil) -> Alphabet? {
        let waAlphaPtr: UnsafePointer<wa_alphabet>?

        if let script = script {
            waAlphaPtr = code.withCString { codeCStr in
                script.withCString { scriptCStr in
                    return wa_load_alphabet(codeCStr, scriptCStr)
                }
            }
        } else {
            waAlphaPtr = code.withCString { codeCStr in
                return wa_load_alphabet(codeCStr, nil)
            }
        }

        guard let waAlpha = waAlphaPtr?.pointee else { return nil }

        let language = String(cString: waAlpha.language)
        let scriptStr = String(cString: waAlpha.script)

        var uppercase: [String] = []
        if waAlpha.uppercase_len > 0, let items = waAlpha.uppercase {
            for i in 0..<Int(waAlpha.uppercase_len) {
                if let cStr = items[i] { uppercase.append(String(cString: cStr)) }
            }
        }

        var lowercase: [String] = []
        if waAlpha.lowercase_len > 0, let items = waAlpha.lowercase {
            for i in 0..<Int(waAlpha.lowercase_len) {
                if let cStr = items[i] { lowercase.append(String(cString: cStr)) }
            }
        }

        var digits: [String] = []
        if waAlpha.digits_len > 0, let items = waAlpha.digits {
            for i in 0..<Int(waAlpha.digits_len) {
                if let cStr = items[i] { digits.append(String(cString: cStr)) }
            }
        }

        var frequency: [String: Double] = [:]
        if waAlpha.frequency_len > 0, let freqItems = waAlpha.frequency {
            for i in 0..<Int(waAlpha.frequency_len) {
                let entry = freqItems[i]
                if let cStr = entry.ch {
                    frequency[String(cString: cStr)] = entry.freq
                }
            }
        }

        return Alphabet(
            language: language,
            script: scriptStr,
            uppercase: uppercase,
            lowercase: lowercase,
            digits: digits,
            frequency: frequency
        )
    }

    /// Load frequency list for a given language code
    public static func loadFrequencyList(code: String) -> FrequencyList? {
        let waFreqPtr = code.withCString { cString in
            return wa_load_frequency_list(cString)
        }

        guard let waFreq = waFreqPtr?.pointee else { return nil }

        let language = String(cString: waFreq.language)
        let mode = String(cString: waFreq.mode)

        var tokens: [String] = []
        if waFreq.token_count > 0, let items = waFreq.tokens {
            for i in 0..<Int(waFreq.token_count) {
                if let cStr = items[i] { tokens.append(String(cString: cStr)) }
            }
        }

        return FrequencyList(language: language, mode: mode, tokens: tokens)
    }

    /// Detect languages from text
    public static func detectLanguages(text: String, candidateLangs: [String]? = nil, topK: Int = 3) -> [DetectResult] {
        return text.withCString { textCStr in
            var resultsArray: wa_detect_result_array

            if let candidates = candidateLangs {
                // Convert array of strings to array of C strings
                var cStrings: [UnsafePointer<CChar>?] = []
                for candidate in candidates {
                    candidate.withCString { cStr in
                        // We must duplicate the string because withCString closure scope
                        cStrings.append(strdup(cStr))
                    }
                }

                resultsArray = wa_detect_languages(textCStr, cStrings, cStrings.count, nil, 0, topK)

                // Free the duplicated C strings
                for ptr in cStrings {
                    if let ptr = ptr { free(UnsafeMutableRawPointer(mutating: ptr)) }
                }
            } else {
                resultsArray = wa_detect_languages(textCStr, nil, 0, nil, 0, topK)
            }

            var results: [DetectResult] = []
            if resultsArray.len > 0, let items = resultsArray.items {
                for i in 0..<Int(resultsArray.len) {
                    let item = items[i]
                    if let langCStr = item.language {
                        results.append(DetectResult(language: String(cString: langCStr), score: item.score))
                    }
                }
            }

            wa_free_detect_results(&resultsArray)
            return results
        }
    }

    /// Get available keyboard layouts
    public static func getAvailableLayouts() -> [String] {
        return stringArrayFromC(wa_get_available_layouts())
    }

    /// Convert C KeyboardLayer to Swift KeyboardLayer
    private static func convertLayer(_ layer: wa_keyboard_layer) -> KeyboardLayer {
        let name = layer.name != nil ? String(cString: layer.name) : ""
        var mappings: [KeyboardMapping] = []
        if layer.entry_count > 0, let entries = layer.entries {
            for i in 0..<Int(layer.entry_count) {
                let entry = entries[i]
                let val = entry.value != nil ? String(cString: entry.value) : ""
                mappings.append(KeyboardMapping(keycode: entry.keycode, value: val))
            }
        }
        return KeyboardLayer(name: name, entries: mappings)
    }

    /// Convert C KeyboardLayout to Swift KeyboardLayout
    private static func convertLayout(_ layout: wa_keyboard_layout) -> KeyboardLayout {
        let id = layout.id != nil ? String(cString: layout.id) : ""
        let name = layout.name != nil ? String(cString: layout.name) : ""

        var layers: [KeyboardLayer] = []
        if layout.layer_count > 0, let cLayers = layout.layers {
            for i in 0..<Int(layout.layer_count) {
                layers.append(convertLayer(cLayers[i]))
            }
        }
        return KeyboardLayout(id: id, name: name, layers: layers)
    }

    /// Load keyboard layout
    public static func loadKeyboard(layoutId: String) -> KeyboardLayout? {
        let waLayoutPtr = layoutId.withCString { cStr in
            return wa_load_keyboard(cStr)
        }
        guard let waLayout = waLayoutPtr?.pointee else { return nil }
        return convertLayout(waLayout)
    }

    /// Find layouts by HID usage
    public static func findLayoutsByHid(hidUsage: UInt16, layerName: String) -> [LayoutMatch] {
        return layerName.withCString { layerNameCStr in
            var matchArray = wa_find_layouts_by_hid(hidUsage, layerNameCStr)
            var results: [LayoutMatch] = []

            if matchArray.len > 0, let items = matchArray.items {
                for i in 0..<Int(matchArray.len) {
                    let match = items[i]
                    if let layoutPtr = match.layout, let layerPtr = match.layer, let mappingPtr = match.mapping {
                        let layout = convertLayout(layoutPtr.pointee)
                        let layer = convertLayer(layerPtr.pointee)
                        let mappingVal = mappingPtr.pointee.value != nil ? String(cString: mappingPtr.pointee.value) : ""
                        let mapping = KeyboardMapping(keycode: mappingPtr.pointee.keycode, value: mappingVal)

                        results.append(LayoutMatch(layout: layout, layer: layer, mapping: mapping))
                    }
                }
            }

            wa_free_layout_matches(&matchArray)
            return results
        }
    }
}
