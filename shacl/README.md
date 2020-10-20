**Validate workflows with PLEX SHACL restrictions**
```
pyshacl -s plex_shapes.ttl -m -i rdfs -a -f human ../ml-classify-text/rdf/ml-classify-text.ttl 
```
