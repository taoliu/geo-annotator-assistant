import json
import gzip

def open_file(filename, mode):
    """Open a file intelligently, using gzip.open if it's gzipped, or open if not."""
    with open(filename, 'rb') as f:
        magic_number = f.read(2)
    if magic_number == b'\x1f\x8b':
        # The file is gzipped
        return gzip.open(filename, mode)
    else:
        # The file is not gzipped
        return open(filename, mode)


def gse_dict_to_prompt(gse_dict): # this is for gsm!
    prompts = []
    
    for gsm_id, sample_entry in gse_dict.items():
        series = sample_entry.get("series", {})
        platform = sample_entry.get("platform", [{}])[0]  # Assume first platform (why??)
        sample_data = sample_entry.get("sample_data", {})

        content_text = (
            f"Series Accession: {series.get('series gse accession', 'N/A')}\n"
            f"Sample ID: {gsm_id}\n"
            f"Sample Title: {sample_data.get('sample title', 'N/A')}\n"
            f"Sample Organism: {sample_data.get('sample organism', 'N/A')}\n"
            f"Sample Molecular: {sample_data.get('sample molecular', 'N/A')}\n"
            f"Sample Library Selection: {sample_data.get('sample library selection', 'N/A')}\n"
            f"Sample Library Source: {sample_data.get('sample library source', 'N/A')}\n"
            f"Sample Library Strategy: {sample_data.get('sample library strategy', 'N/A')}\n"
            f"Sample Source Name: {sample_data.get('sample source name', 'N/A')}\n"
            f"Sample Extract Protocol: {sample_data.get('sample extract protocol', 'N/A')}\n"
            f"Sample Characteristics: {sample_data.get('sample characteristics', 'N/A')}\n"
            f"Sample Filename: {sample_data.get('sample filename', 'N/A')}\n"
            f"Series Title: {series.get('series title', 'N/A')}\n"
            f"Series Summary: {series.get('series summary', 'N/A')}\n"
            f"Series Filename: {series.get('series filename', 'N/A')}\n"
            f"Platform: {platform.get('platform title', 'N/A')} ({platform.get('platform technology', 'N/A')})\n"
        )
        prompts.append({"content_text": content_text, "gsm_accession": gsm_id, "gse_accession": series.get("series gse accession", "N/A")})

    return prompts
