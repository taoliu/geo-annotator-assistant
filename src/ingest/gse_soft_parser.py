import re
import json
from GEOparse import get_GEO
import random

random.seed(1234)

# Constant
sample_field_names = {
    "sample organism": "organism_ch1",
    "sample molecular": "molecule_ch1",
    "sample library selection": "library_selection",
    "sample library source": "library_source",
    "sample library strategy": "library_strategy",
    "sample title": "title",
    "sample source name": "source_name_ch1",
    "sample extract protocol": "extract_protocol_ch1",
    "sample characteristics": "characteristics_ch1",
    "sample filename": "supplementary_file_1"
}


def extract_sample_level_data(input_soft_file):
    """Read content from a SOFT file and return a dictionary where each
    entry corresponds to a sample (GSM). Each sample entry will include
    the GSE metadata, platform data, and sample data.
    """
    try:
        gse = get_GEO(filepath=input_soft_file, geotype='GSE', silent=True)
    except Exception:
        print(f"Error occurs while reading {input_soft_file}")
        return None

    metadata = gse.metadata
    samples = gse.gsms
    platforms = gse.gpls

    # Extract common GSE-level metadata
    gse_metadata = __get_gse_data(metadata)
    platform_data = __get_platform_data(platforms)

    # Build a dictionary at the sample level
    sample_level_dict = {}

    if len(samples) == 0:
        return None  # No samples, return nothing

    for gsm_id, sample in samples.items():
        sample_data = sample.metadata

        sample_entry = {
            "series": gse_metadata,  # Embed GSE-level metadata
            "platform": platform_data,  # Embed platform data (same for all samples in a GSE)
            "sample_id": gsm_id,
            "sample_data": __extract_sample_metadata(sample_data)
        }

        sample_level_dict[gsm_id] = sample_entry

    return sample_level_dict


def __get_gse_data(metadata):
    return {
        'series gse accession': "\n".join(metadata.get('geo_accession', [''])),
        'series title': "\n".join(metadata.get('title', [''])),
        'series summary': "\n".join(metadata.get('summary', [''])),
        'series overall design': "\n".join(metadata.get('overall_design', [''])),
        'series type': "\n".join(metadata.get('type', [''])),
        'series filename': "\n".join(metadata.get('supplementary_file', ['']))
    }


def __get_platform_data(platforms):
    platform_entries = []
    for _, platform in platforms.items():
        platform_data = platform.metadata
        platform_entries.append({
            'platform title': "\n".join(platform_data.get('title', [''])),
            'platform technology': "\n".join(platform_data.get('technology', [''])),
            'platform organism': "\n".join(platform_data.get('organism', ['']))
        })
    return platform_entries


def __extract_sample_metadata(sample_data):
    sample_dict = {}

    for field, geo_key in sample_field_names.items():
        sample_dict[field] = "\n".join(sample_data.get(geo_key, ['']))

    return sample_dict


# Example call
# if __name__ == "__main__":
#     input_soft_file = "your_file.soft"  # Change to your actual file
#     sample_dict = extract_sample_level_data(input_soft_file)
#     if sample_dict:
#         print(json.dumps(sample_dict, indent=2))