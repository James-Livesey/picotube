# picotube
The world's smallest online video streaming site™

## Prerequisites
Before running picotube, first install the required packages by running:

```bash
pip3 install -r requirements.txt
```

## Running picotube
To run picotube, you need to run these two commands concurrently:

```bash
python3 app/main.py
```

```bash
python3 -m pipelines.main
```

The picotube interface will then be available at [localhost:8000](http://localhost:8000).