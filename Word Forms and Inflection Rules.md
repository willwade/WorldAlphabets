# Word Forms and Inflection Rules

[Introduction](#introduction)

[Implementation](#implementation)

[File: words.json](#file:-words.json)

[types](#types)

[antonyms](#antonyms)

[inflections](#inflections)

[File: rules.json](#file:-rules.json)

[rules](#rules)

[id](#id)

[type](#type)

[lookback](#lookback)

[overrides](#overrides)

[inflection](#inflection)

[location](#location)

[tests](#tests)

[substitutions](#substitutions)

[inflection\_locations](#inflection_locations)

[Starting New Language Files](#starting-new-language-files)

[words-en.csv](#words-en.csv)

[rules-en.csv](#rules-en.csv)

[tests-en.csv](#tests-en.csv)

[Future Work](#future-work)

[Changes](#changes)

[Additional References](#additional-references)

# Introduction {#introduction}

We provide a documented and standardized format for tracking word-level information for use by AAC systems. The resulting datasets can be ingested into any AAC system and are built to be language-agnostic, with the intent of allowing new and developing AAC systems to offer more robust functionality without having to recreate the wheel, and making multi-language solutions more approachable.

# Implementation {#implementation}

To accomplish this task, we define two separate but related JSON files that can be paired per language or locale. Both files are JSON files with a simple structure. By convention we use the filenames "words-\<locale\>.json" and "rules-\<locale\>.json" but this isn't necessary.

At their most basic, both files are just JSON hashes. Any top-level attributes whose key name starts with an underscore may be ignored for parsing, and can be used if desired for context-specific implementations. Both files should have a "\_type" attribute with the value of either "words" or "rules" depending on the file's purpose, and a "\_locale" attribute with the value of the specified. NOTE: We assume standardized locale codes with either two-digit ("es" for Spanish) or hyphenated ("zh-TW" for Taiwanese Chinese) codes. We also use the "\_version" attribute with a value of "0.1" to allow for future adjustments.

If you are implementing your own engine, or using this specification to import data for your own purposes, remember that some attributes (specifically "type" which represents part of speech, and "inflection", should support open-ended values, since these attributes may have language-specific values that an English-language system would consider non-standard.

## File: words.json {#file:-words.json}

All other (non-underscored) attributes in the top-level words JSON file should be interpreted as possible words in the current localization. Each word attribute should have the word itself as the key value, and a hash as its value. Words should be lowercase unless they are proper.

Note that the goal should not be to include all possible words in the entire language, but to represent the list of words anticipated to be leveraged in a word-based AAC system. Word tenses may possibly be included as root words themselves, or may be included as inflections for a root word, there is not a standard defined for this.

### types {#types}

Each word must have a types attribute defined, which is an array of parts of speech. Words may have one or multiple parts of speech, and the first value is considered the default or most common type for the word. Values in the list of parts may be language-specific if appropriate, but the following types should be expected and supported in the interface for an English-language AAC system: \[noun, verb, adjective, adverb, pronoun, numeral, determiner, social, preposition, conjunction, interjection, question\]. For example, many AAC systems choose a different color to represent buttons of different types of speech.

### antonyms {#antonyms}

This optional attribute has for its value an array of strings, representing possible antonyms for the specified word. The first item in the list is considered the default antonym.

### inflections {#inflections}

The (required) inflections attribute has a hash for its value with sub-attributes defining different inflections for the word. For example, verbs would include different tenses, nouns would include proper pluralization, etc. The attribute key names can be language-specific if needed, as the important thing is that they match the values used in the rules.json file for rules and inflection\_locations. If working with an already-populated language, refer to examples within the file before adding new words to ensure the inflections match what already exists. Note that words with multiple parts of speech will have inflections for different parts of speech (in English a verb that is also a noun will have a "simple\_past" attribute and also a "plural" attribute).

Additionally there is a "regulars" attribute. This attribute is not required, but may be used to save space for implementation. Basically if the AAC system is known to have a built-in mechanism for handling inflections, and any of the word's inflections match what the mechanism would generate, then the inflection type can be included in the list of regulars so the system doesn't need to store that particular inflection. For example, for the word "jump", the "present\_participle" inflection is "jumping", which fits the standard rules for inflecting a verb, so "present\_participle" could be included in "regulars" for the word "jump". However, for the word "forget", the "simple\_past" inflection is "forgot", not "forgetted", so this would not be included in the list of regulars.

Optionally there are uppercase cardinal direction attributes ("N", "SW", "E") that can be used as manual overrides for cardinal inflections. These cardinal inflections are clarified in the "inflection\_locations" section of the "rules.json" file type.

## File: rules.json {#file:-rules.json}

The rules JSON file includes inflection rules and conventions to make it easier for AAC systems to support common or standardized word inflections for their users. It contains a few top-level attributes, as defined below. Any other top-level attributes should be prefixed with an underscore to avoid future collisions. As with the words JSON, note that the purpose of the data is not to encapsulate all possible inflection rules, but instead to provide "common-sense" support for grammatical inflections. 

Many AAC users can benefit from sounding more natural, and the defined rules should exist to help with this cause without causing undue complexity or confusion. Where there is too much ambiguity, it is probably better to have no matching rules than to have a rule auto-applied that only works half the time. As such we recommend a combination of both simple auto-inflections (that a user can disable if desired) as well as a straightforward mechanism for manually applying inflections, or for repairing mis-applied inflections.

The general algorithm for applying rules is, for all visible buttons, to consider the sequence of already-selected words and try to match it against a list of possible rules, stopping at the first matching rule for that button. Then this rule is used to apply an inflection type or cardinal inflection and update the interface accordingly. Any change to the sequence of already-selected words would trigger a re-evaluation.

### rules {#rules}

The rules attribute has for its value an array of hashes, each defining a different inflection rule. For example, in English you could have a rule that says if the user says "I like" then the next verb would be better suited with an infinitive inflection ("I like to jump") than a standard one ("I like jump"). Each rule has the following possible attributes

#### id {#id}

Each rule should have a unique string for its identifier. This is mainly used for testing, but can also help with debugging and for general reference.

#### type {#type}

Each rule should have a type attribute defined. This attribute could have as its value one of the parts of speech defined for the language, or "override" as a special type. This is used by the AAC system to filter the rule to only buttons whose associated word matches the specified type as its default type.

#### lookback {#lookback}

This attribute contains an array of criteria that are used by the AAC system to try to match against the already-selected sequence of words. Each lookback can be "optional" in which case it can be skipped or considered when comparing, and may include an array of specifically-matching "words", or a "type" representing a part of speech. Lookback items with "type" defined may also include "match" or "non\_match" attributes whose values are a string to be converted into a regular expression by the parsing engine.

Additionally, each lookback item may optionally include a "condense" attribute. If this value is true, then if the inflected button is added to the sentence, the words in the already-selected sequence which match condensable lookbacks should be removed from the sentence. This functionality is useful for languages where pronoun inclusion is either superfluous or irrelevant ("pro-drop" languages, such as Spanish, Polish, etc.), but may serve other purposes as well. The "condense" feature is considered an advanced feature and support is not required, but is recommended for AAC systems supporting any pro-drop languages.

#### overrides {#overrides}

If the rule is of type "override" then it must have an "overrides" hash defined, which includes a mapping of words to their inflections. For example, in English "is" can be overridden to "am" not for all pronouns, but specifically for the pronoun "I".

#### inflection {#inflection}

For non-override rules, the "inflection" attribute defines which inflection type to retrieve from the word JSON to apply for any words that match the specified rule.

#### location {#location}

As an optimization, rules can also include a "location" attribute. This attribute should follow the same rules defined in the "inflection\_locations" section, and uses a lowercase cardinal direction to define where the inflection may be found for the specified word. Note that AAC systems that rely on the "location" optimization (such as CoughDrop) will only be able to support up to 8 auto-inflection rule types (one per cardinal direction or sub-direction) per part of speech, so for languages with more than 8 verb conjugations, consider which inflections will have the most "bang for their buck" and set rules at least for those.

### tests {#tests}

This contains an array of validation tests that are used to ensure that the specified rules properly follow language conventions. This can be useful during content development, and also during AAC system implementation. Each test is itself an array of the following values, \[pre-text, word, post-text, additional checks\]. The pre-text is a string representing all words already-selected by the user. The post-text should be a string representing the resulting sentence after the user has selected the word.

The additional checks allow for checking that the expected rule was applied correctly. It may include "rule\_id" to compare against the list of rules, and "inflection" to check that the correct inflection was applied.

### substitutions {#substitutions}

This section is entirely optional, and is used by some implementations to support both a hash of all known "contractions", and a hash of "default\_contractions" which may possibly be applied without user confirmation.

### inflection\_locations {#inflection_locations}

The cardinal inflections concept is an optimization meant to make grammatical support more approachable. Some AAC systems support long-pressing or swiping to apply different verb tenses or other word forms. This can be much more approachable for an AAC user than having separate buttons for all possible tenses or other inflections. For languages that have a relatively small set of common inflections, the list can be displayed as a frame or border surrounding the base form of the word. We take this application and codify it using cardinal directions, which makes it possible for users to learn to apply inflections consistently without having to learn tense locations for every possible word. Instead, they could learn that, for example, infinitive forms would always be to the right ("e") or that plural forms would always be up ("n"). In some systems this is implemented as a shortcut, so the user can long-press to pull up the grid of inflections, but once they are comfortable they can also just swipe in that direction to apply the inflection without needing to wait for a long-press.

The inflection\_locations attribute is a hash of parts of speech, where each part of speech has a value of an array of criteria. The first or first few criteria are hashes with the "required" attribute defining a specific attribute that is required before a word from the words JSON may be considered. Subsequent criteria have a "location" attribute defining a cardinal direction ("n" north, "sw" for southwest, "e" for east, "c" for center, etc.), an "inflection" attribute for which inflection type should be placed in that cardinal location, and a few additional options defined in the next paragraph. Unless otherwise specified, each cardinal location should be populated with the first criteria that matches and actually has a value defined on the word form the words JSON.

Note that because some AAC systems (such as CoughDrop) rely on an optimization and do not send all possible inflections to the user's interface, but only those mapped to cardinal directions, there is a limit of 8 possible inflections per word. In practice this means that verbs can only have up to 8 inflections, adjectives only 8, etc. Some languages have dozens of different inflections, and while it may make sense to add these to the words.json file, only those mapped to a cardinal location will appear in the user interface and be considered when updating buttons based on inflection rules.

The following optional attributes may be defined on each criteria. The "type" attribute means the criteria should only be applied for words that have both originally-specified part of speech and this additional part of speech. The "if\_empty" criteria should only be applied if no previous criteria have caused any content to be populated. The "override\_if\_same" criteria should only  be applied if the current value for the "location" attribute is the same as the value specified (for example, "location":"n", "inflection":"past","override\_if\_same":"c" means override what is currently in the "n" location with the "past" inflection if what is in the "n" location currently matches exactly what is in the "c" location).

# Starting New Language Files {#starting-new-language-files}

For non-technical users, it will be easiest to use the CSV format for creating an initial data set. The web site has built-in tools for converting CSV files into the structured JSON format required for the engine to operate. You can download any of the existing data files as a CSV to see how they are structured. Below we will outline the basic format of each of the three CSV files that are available, based on what you will see if you download the English CSV files. Note that all the CSV files contain a header row, and that most of the header values are required to remain in English (for now) unless otherwise indicated.

### words-en.csv {#words-en.csv}

The first six columns (word, type1, type2, type3, antonym1, antonym2) are the only required columns for this file. Some words can have more than one grammatical type ("academic" is both an adjective and a noun), so we support multiple types, ordered by priority. The same is true for antonyms. Note that the values for the type columns do NOT need to be English grammatical names. They can be named whatever makes sense in your data set, and as long as the same values are used in the "type" column in the rules file, the engine should be able to handle it correctly.

We also strongly encourage but do not require a seventh column, "base". This would be the uninflected form of the word ("laughing" would have "laugh" as its base, "jump" would have "jump" as its base). 

After these required column headers, you may name the rest of the columns whatever you would like. The English file includes columns like plural, possessive, infinitive, etc. but the headers can be in whatever language you like, as long as the same values are used in the "inflection" columns in the rules and tests files. The column list should include all possible inflections for all different parts of speech. In general the grid will be fairly sparse, as many words will only be inflected for a few columns based on their part of speech, but words can in theory support all possible inflections.

### rules-en.csv {#rules-en.csv}

The rules file is the most complex, because it contains the most-structured data. If you view it in a visual editor like Excel or Sheets the layout should be relatively straightforward. Each rule contains an ordered list of lookbacks, and if all those lookbacks are met, then the rule will be triggered by the engine. Rules are either manually-defined sets of overrides, or defined to update to a specified inflection (or cardinal location) from the words data set. Two of the columns, lookbacks\_words\_or\_overrides\_pre and lookbacks\_type\_or\_overrides\_post, contain different values depending on the current subtype (hence the long names). For lookback rows, the words column is a list of all matching words separated by a vertical bar "|". The final two columns, lookbacks\_optional	and lookbacks\_condense, are true/false columns that will evaluate to FALSE unless the value is "1".

This file will be easiest to generate from an existing example, and all the column names are required so you can edit it in-place if you like.

### tests-en.csv {#tests-en.csv}

The web interface automatically runs the specified test cases to ensure that the correct inflections are being recommended, and that the expected rules are being matched and triggered. The 5 columns for the tests file are standard and are required headers. The first two columns are optional for each row, but will help with identifying the expected result, which can aid in troubleshooting when any of the tests fail. The final three columns let you define the words leading up to the current word, the word in question, and the expected result based on applying the rule.

# Future Work {#future-work}

Currently only English language files have been created. Based on our experience building multi-language support into AAC systems, we have tried to build accommodations for additional languages, but those accommodations are likely incomplete. 

It is worth noting, however, that when working with teams for other languages, at times what seems like too much emphasis is placed on supporting all possible rules to accomplish a grammatically flawless implementation. We obviously cannot speak for the "best" way to implement in each language, and AAC users need to be understood by their speech output, but care should be taken to strike the appropriate balance between 1\) what listeners expect to hear a language sound like, 2\) what AAC systems can reasonably implement, and 3\) what an AAC user can efficiently generate without requiring extensive up-front training. In English, a beginning AAC user can make their intentions known and share a broad variety of ideas with incorrect grammatical tenses ("he want stop", "I no like", etc.), and still generally be understood, and it seems likely that this would also be possible in other languages. More advanced users will be able to leverage tools like keyboards and manual inflections, while beginning users should be able to adopt an AAC system without too many hurdles, all while still hopefully getting over the hump of listener comprehension.

Additionally, we need to add some sort of linguistic mapping. A German-based dataset should be able to use German headers or key values to make it more approachable for folks to contribute, but where possible it would be helpful to be able to map those back to a standardized set of attribute names for things like consistent button coloring based on parts of speech. Maybe, based on the language, it makes more sense to have a color mapping than to try to shoe-horn it back to English-language concepts.

# Changes {#changes}

9/25/24 \- Added notes on CSV files for easier dataset generation

# Additional References {#additional-references}

* [words-en.json example](https://tools.openaac.org/inflections/words-en.json)  
* [rules-en.json example](https://tools.openaac.org/inflections/rules-en.json)

![88x31.png][image1]OpenAAC. 2024

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFgAAAAfCAYAAABjyArgAAAFlElEQVR4Xu2azU5bRxTHva4UxJ4Ny7CjrdJlipQ+AH2AVLxBUXeRqIIiUilSJYSoonbRUKm7JsF8fxpswHzaxjaBbHkEHuF0fnM51+O5NmBjX5yEI/2l6/k4M/rfM/85M9cJEelKJBJyj9bDWAKzPxbXFmQ5tSSrmyuS2lqXzZ1N2drNyM7Bjuwd7cpBfl8OC4eSOz6SfDEn+VI+gHnOFY/kyNTRhrZZ04e+aeMDX6ubq9Y3Y8yvzMns8ozMLCZleuG9vJ9/Z/Fu7q28nf3vs4FDdIXctfSqbGynJJNNy87+tiXrsHBgCTwuF6T0oSjl05KcnJ3Ih48BeC6flm0dbXKGcPrQFx+Z3bT1iW+f5OTidEgyBH+mJCeqyTWRRwTu5/ZttEIapI69HJMnPzyRB10PIkuBMurGfhuzbY9Pju1LIaKzh1kbzRvbG1Ukz63MysxSMiB5vkKyP8lG8WzkmfT19UXmSBl1fvt2IiQYWXDJhZh8KWejcmJyQnp6eiITrgfaTvwxYfsiIUTzbkhyKpSLhdV5mVsOSG5FFE/+OSkP+x6G8xgYGJDh4WELnrWcNrT1+7cDl2MmrE4iCxVy8zYSB38crCKvu7tbhoaGZHR0VNLptAXPlFHntqVvdn9HCuWAZCIZuQg0eUWW1herpeIWUTz17xvp6uoKxh0clPPzczaYKqOMOtrQNg6SQ4LZ0NBLZIHI9cmFPIi8uLjw511lU1NTVUQTLZDMC+PFMQYb33pmTVY2lgOpqBHF/kSvg0YuL9o1nYdrzFHn5vtpNUKCWb5sSmguS9slt7+/v2ZE1DNeAn20P77wiSYzRkUqnCheMlG8MN2UTKCrdhwTnR/PzqrmUotgTCO53ZocEkwqdpA/sBsamuuSe13U1jKfZDSZjc9KhRkrnQ2i2GrxWqDFKhONEqwbWiNBQFv60Nf310qEBNvoNRGGNOiGxlIvFov+3G5skKxygU98k8JpFKe2gih2M4pmZAL/bGK+IRf6gn3pwHTj8/21EiHB6GPBRC+pmE4Kzb2tqd4BUjhWiGrx5mXa5spEswSTKfim4yp8o09sBHNCKxqdJJflN5HnSgPZArrFWwcu+X7d+Ph4WIdpFOMbLebEF5EJk7LZbMLRYX+y9fBJEMzmxhLWQ4S7pCDQnyyAzGQyGSn3++tSxTcnPqSIvJiUbT2zbrMJdFjTtWYI7niJ4D7h5KwcTsiNQt2sent77eYA4Tyz/LVOMw0I1zo1VyY4VjNWRYcDgjVda4bgqzY5Hde32Dc5cl/uFXRCkKimZbU0+ao6NXcFMAY58d7RXssIdtM03+oRHHua9ikTDBo5aKj2xnrQuKlEsPGRuvEMqa5E+HVq7ZYI0PFH5as2uas2sqvq1DRigk2uZMdq5SangGT3soeXzjwY3z303Mllj6ZpekQmtXLNT8XcCIVkLffrMCIan5qmMZamaWvp26dpPjryulIPGu4x2c9nm7F6B43ty4MGV5d60Gj2JNfJCAnePax9VK6lZTe1uI7KnYyQYPey580/f4dR17LLHrMy8M1lD2PplaV78d7sZU8nIyQYjDwfCa8rn/70tIrkRi59iPqa15XG94uXL8LyLwiVH8O//GzTqNJp4xfu1NHGvXB/9N0jKw3k2bzAGoN/Cagu+NUQwWEAkt1IBo1+MoLcgvH1+q/X/qBtgWtumd/G79dmRAoCkolks7TR5IY/ek7qR89cbOSCesTq8x2QCyIFFsiF+9ke0q77bM+XC/vZnv9HmL5xy4Jrter8spgQKQjxzbdfS3IuaVM48mQOI8EfT8rOH0/Ktsz948nMfFIef/844q/dcEn0CfV/x4hIQQSQ9er3V5LKpJy/Tl2Cv06ZMupocxfEKlyrVeeXxYRIwT1aCfNiv4oU3qMlYNH8D8YjNDMPmXCyAAAAAElFTkSuQmCC>