# Vector Search 

imagine you're looking for something on the internet, right?

Usually, when you type words into a search bar, the computer tries to find exactly those words. That's like when you ask for 'nipples' and it shows you pictures of nipples. That works great if you know exactly what you're looking for, and if what you're looking for is words.

![nipples](assets/nipples-one.jpg)

But what if you're looking for a picture of a cassette, but you don't know the word 'cassete'? Or what if you want to find a song that sounds like another song, but you don't know the song's name? Or what if you're trying to find a video that just feels like a funny cat video, even if it doesn't say 'funny cat' anywhere?

Or even with words, sometimes different words can mean the same thing, right? Like 'big car' and 'large automobile'. If you search for 'big car', you might miss 'large automobile' if the computer only looks for exact words.

This is where 'vector search' comes in!

Think of it like this: instead of just matching words, vector search turns everything – pictures, sounds, videos, words, ideas – into special numbers. These numbers are like a secret code that tells the computer what something means or what it looks like inside its brain.

So, if two things mean something similar, their 'numbers' will be very close to each other.

Then, when you search, the computer just looks for the 'numbers' that are super close to what you're looking for. This way, it can find things that are similar in meaning, even if they don't use the exact same words, or even if they're not words at all! It's like it understands the idea of what you want, not just the words.

## Step 0: Setup Qdrant
[Qdrant](https://qdrant.tech/) is fully open-source, which means you can run it in multiple ways depending on your needs.
You can self-host it on your own infrastructure, deploy it on Kubernetes, or run it in managed Cloud.

We're going to run a Qdrant instance in a Docker container.

```bash
docker run -p 6333:6333 -p 6334:6334 \
   -v "/path/to/local/qdrant_storage:/qdrant/storage:z" \
   qdrant/qdrant
```
The second line in the docker run command mounts local storage to keep your data persistent. So even if you restart or delete the container, your data will still be stored locally.

```
6333 – REST API port
6334 – gRPC API port
```

To help you explore your data visually, Qdrant provides a built-in Web UI, available in both Qdrant Cloud and local instances. You can use it to inspect collections, check system health, and even run simple queries.

When you're running Qdrant in Docker, the Web UI is available at http://localhost:6333/dashboard

### Installing Required Libraries

In the environment we’ll install the qdrant-client package.
The fastembed package - an optimized embedding (data vectorization) solution designed specifically for Qdrant. Make sure you install version >= 1.14.2 to use the local inference with Qdrant.

```bash
uv pip install "qdrant-client[fastembed]>=1.14.2"
```

## Step 1: Import Required Libraries & Connect to Qdrant
## Step 2: Study the Dataset
## Step 3: Choosing the Embedding Model with FastEmbed

FastEmbed is an optimized embedding solution designed specifically for Qdrant. It delivers low-latency, CPU-friendly embedding generation, eliminating the need for heavy frameworks like PyTorch or TensorFlow. It uses quantized model weights and ONNX Runtime, making it significantly faster than traditional Sentence Transformers on CPU while maintaining competitive accuracy.

FastEmbed supports:

- **Dense embeddings** for text and images (the most common type in vector search, ones we're going to use today)
- **Sparse embeddings** (e.g., BM25 and sparse neural embeddings)
- **Multivector embeddings** (e.g., ColPali and ColBERT, late interaction models)
- **Rerankers**

### Model

```python
model_handle = "jinaai/jina-embeddings-v2-small-en"
```

Like most dense embedding models, `jina-embedding-small-en` was trained to measure semantic closeness using cosine similarity.
You can find this information, for example, on the model’s [Hugging Face card](https://huggingface.co/jinaai/jina-embeddings-v2-small-en).

>The parameters of the chosen embedding model, including the output embedding dimensions and the semantic similarity (distance) metric, are required to configure semantic search in Qdrant.

## Step 4: Create a Collection

When creating a [collection](https://qdrant.tech/documentation/concepts/collections/), we need to specify:

Name: A unique identifier for the collection.
Vector Configuration:
Size: The dimensionality of the vectors.
Distance Metric: The method used to measure similarity between vectors.
There are additional parameters you can explore in our [documentation](https://qdrant.tech/documentation/concepts/collections/#create-a-collection). Moreover, you can configure other vector types in Qdrant beyond typical dense embeddings (f.e., for hybrid search). However, for this example, the simplest default configuration is sufficient.

```python
# Define the collection name
collection_name = "zoomcamp-rag"

# Create the collection with specified vector parameters
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=EMBEDDING_DIMENSIONALITY,  # Dimensionality of the vectors
        distance=models.Distance.COSINE  # Distance metric for similarity search
    )
)
```
## Step 5: Create, Embed & Insert Points into the Collection

[Points](https://qdrant.tech/documentation/concepts/points/#points) are the core data entities in Qdrant. Each point consists of:

- **ID**. A unique identifier. Qdrant supports both 64-bit unsigned integers and UUIDs.
- **Vector**. The embedding that represents the data point in vector space.
- **Payload** (optional). Additional metadata as key-value pairs.

The speed of upsert mainly depends on the time spent on local inference.
To speed this up, you could run FastEmbed on GPUs or use a machine with more resources.

In addition to basic upsert, Qdrant supports batch upsert in both column- and record-oriented formats.

The Python client offers:

Parallelization
Retries
Lazy batching
These can be configured via parameters in the `upload_collection` and `upload_points` functions.
For details, check the [documentation](https://qdrant.tech/documentation/concepts/points/#upload-points).

### Study Data Visually
Let’s explore the uploaded data in the Qdrant Web UI at [visualize](http://localhost:6333/dashboard#/collections/zoomcamp-rag/visualize) to study semantic similarity visually.

For example, using the Visualize tab in the zoomcamp-rag collection, we can view all answers to the course questions (948 points) and see how they group together by meaning, additionally coloured by the course type.

To do that, run the following command:

```json
{
  "limit": 948,
  "color_by": {
    "payload": "course"
  }
}
```

![visualize.png](assets/visualize.png)

## Step 6: Running a Similarity Search

Now, let’s find the most similar text vector in Qdrant to a given query embedding - the most relevant answer to a given question.

### How Similarity Search Works

1. Qdrant compares the query vector to stored vectors (based on a vector index) using the distance metric defined when creating the collection.
2. The closest matches are returned, ranked by similarity.

> Vector index is built for approximate nearest neighbor (ANN) search, making large-scale vector search feasible.

If you'd like to dive into our choice of vector index for vector search, check our article ["What is a vector database"](https://qdrant.tech/articles/what-is-a-vector-database/), or, for a more technical deep dive, our article on [Filterable Hierarchical Navigable Small World](https://qdrant.tech/articles/filtrable-hnsw/).

Let's define a search function:

```python
def search(query, limit=1):

    results = client.query_points(
        collection_name=collection_name,
        query=models.Document( #embed the query text locally with "jinaai/jina-embeddings-v2-small-en"
            text=query,
            model=model_handle 
        ),
        limit=limit, # top closest matches
        with_payload=True #to get metadata in the results
    )

    return results
```

Now let’s pick a random question from the course data.
As you remember, we didn’t upload the questions to Qdrant.

```python
import random

course = random.choice(documents_raw)
course_piece = random.choice(course['documents'])
print(json.dumps(course_piece, indent=2))

result = search(course_piece['question'])

print(f"Question:\n{course_piece['question']}\n")
print("Top Retrieved Answer:\n{}\n".format(result.points[0].payload['text']))
print("Original Answer:\n{}".format(course_piece['text']))
```

## Step 7: Running a Similarity Search with Filters
We can refine our search using metadata filters.

> Qdrant’s custom vector index implementation, Filterable HNSW, allows for precise and scalable vector search with filtering conditions.

For example, we can search for an answer to a question related to a specific course from the three available in the dataset.
Using a must filter ensures that all specified conditions are met for a data point to be included in the search results.

> Qdrant also supports other filter types such as `should`, `must_not`, `range`, and more. For a full overview, check our [Filtering Guide](https://qdrant.tech/articles/vector-search-filtering/)

To enable efficient filtering, we need to turn on [indexing of payload fields](https://qdrant.tech/documentation/concepts/indexing/#payload-index).

```python
client.create_payload_index(
    collection_name=collection_name,
    field_name="course",
    field_schema="keyword" # exact matching on string metadata fields
)

def search_in_course(query, course="mlops-zoomcamp", limit=1):

    results = client.query_points(
        collection_name=collection_name,
        query=models.Document( #embed the query text locally with "jinaai/jina-embeddings-v2-small-en"
            text=query,
            model=model_handle
        ),
        query_filter=models.Filter( # filter by course name
            must=[
                models.FieldCondition(
                    key="course",
                    match=models.MatchValue(value=course)
                )
            ]
        ),
        limit=limit, # top closest matches
        with_payload=True #to get metadata in the results
    )

    return results

print(search_in_course("What if I submit homeworks late?", "mlops-zoomcamp").points[0].payload['text'])
```

