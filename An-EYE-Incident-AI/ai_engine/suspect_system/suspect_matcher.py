from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def find_matching_suspect(new_embedding, suspects):

    best_match = None
    best_score = 0

    for suspect in suspects:

        if "embedding" not in suspect:
            continue

        old_embedding = np.array(
            suspect["embedding"]
        ).reshape(1, -1)

        new_embedding_np = np.array(
            new_embedding
        ).reshape(1, -1)

        similarity = cosine_similarity(
            old_embedding,
            new_embedding_np
        )[0][0]

        if similarity > best_score:

            best_score = similarity
            best_match = suspect

    return best_match, best_score