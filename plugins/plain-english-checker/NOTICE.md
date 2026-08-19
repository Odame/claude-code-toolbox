# Third-party data bundled with plain-english-checker

## MAGPIE corpus — `src/plain_english_checker/idioms.txt`

The idiom check matches against `idioms.txt`, a list built from the MAGPIE corpus.

- **Work**: MAGPIE: A Large Corpus of Potentially Idiomatic Expressions
- **Authors**: Hessel Haagsma, Johan Bos, Malvina Nissim
- **Source**: https://github.com/hslh/magpie-corpus
- **Paper**: Proceedings of the Twelfth Language Resources and Evaluation Conference
  (LREC 2020), pages 279-287, European Language Resources Association.
  http://www.lrec-conf.org/proceedings/lrec2020/pdf/2020.lrec-1.35.pdf
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/

CC BY 4.0 asks for attribution and for a statement of any change made. This file is that
attribution. The change: `idioms.txt` holds only the distinct values of the `idiom` field,
sorted, with the rest of each corpus record dropped. No idiom string itself was edited.

The list was built from `MAGPIE_unfiltered.jsonl`, which covers all 1,756 idiom types the
corpus annotates, rather than from the filtered splits, which drop instances by annotation
confidence and sense label. Sense labels mark whether one instance is used idiomatically or
literally, and this check needs the idiom types themselves, so the unfiltered file is the
right source. Rebuild the list with:

```
curl -O https://raw.githubusercontent.com/hslh/magpie-corpus/master/MAGPIE_unfiltered.jsonl
python3 -c "
import json
idioms = set()
with open('MAGPIE_unfiltered.jsonl') as corpus:
    for line in corpus:
        if line.strip():
            idioms.add(json.loads(line)['idiom'])
for idiom in sorted(idioms, key=str.lower):
    print(idiom)
"
```

Keep the comment header of `idioms.txt` when rebuilding it: `#` lines are skipped at load.
