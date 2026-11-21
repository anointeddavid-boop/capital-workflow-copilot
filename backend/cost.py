# Prices in US dollars per million tokens for the Haiku model.
# These are list prices. Check Anthropic's pricing page and update them if they changed.
INPUT_PER_MILLION = 1.00
OUTPUT_PER_MILLION = 5.00


def estimate_cost(tokens_in, tokens_out):
    return (tokens_in * INPUT_PER_MILLION + tokens_out * OUTPUT_PER_MILLION) / 1_000_000
