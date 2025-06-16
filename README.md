# (WIP) LLM Zoomcamp

![logo](/assets/logo.jpg)

This repository follows the LLM Zoomcamp from [DataTalksClub](https://github.com/DataTalksClub/llm-zoomcamp) - A Free Course on Real-Life Applications of LLMs.

## ElasticSearch

```bash
docker run -it \
    --rm \
    --name elasticsearch \
    -m 4GB \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    docker.elastic.co/elasticsearch/elasticsearch:8.17.6
```