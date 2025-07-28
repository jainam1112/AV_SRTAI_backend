import srt

def parse_srt(srt_text):
    subs = list(srt.parse(srt_text))
    chunks = []
    for sub in subs:
        chunks.append({
            "start": str(sub.start),
            "end": str(sub.end),
            "text": sub.content
        })
    return chunks
