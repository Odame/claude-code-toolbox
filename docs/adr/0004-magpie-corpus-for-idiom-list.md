# Source the idiom list from the MAGPIE corpus

The idiom check needs a list of English idioms to match against, without hand-curating every entry. No actively-maintained, purpose-built PyPI idiom package has a clean redistribution license: `englishidioms` extracts from a commercial dictionary with unclear rights, and the Wiktionary idiom category is CC-BY-SA (share-alike — would obligate the plugin's license terms). We're extracting idiom strings from the MAGPIE corpus (1,756 idiom types, CC-BY-4.0, attribution-only) and bundling them as a static plain-text file, matched with the existing exact-phrase regex matcher — base/citation forms only, no inflection handling (see ADR-0005).

## Considered Options

- **`englishidioms` PyPI package** — largest list (22k+ entries), but sourced from a commercial dictionary with unclear redistribution rights.
- **Wiktionary idiom category** — larger (~10,600 entries), but CC-BY-SA share-alike license.
- **MAGPIE corpus, extracted list** (chosen) — smaller (1,756 types) but clean CC-BY-4.0 attribution-only license and real linguistic provenance, not AI-generated.
