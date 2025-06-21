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
## Step 4: Create a Collection
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
These can be configured via parameters in the upload_collection and upload_points functions.
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
