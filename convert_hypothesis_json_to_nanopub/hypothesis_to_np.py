import json
import rdflib
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, XSD, OWL
from fairworkflows import Nanopub

# Read in the json file (exported from hypothesis)
with open('test.json') as infile:
    data = json.load(infile)

    # Loop through every annotation entry in the json
    for entry in data:

        # Get whatever information you want for your manual step description
        url = entry['url']
        prefix = entry['prefix']
        exact = entry['exact']
        suffix = entry['suffix']
        title = entry['title']

        # print(f'url={url}\nprefix={prefix}\nexact={exact}\nsuffix={suffix}\ntitle={title}')

        # Now make assertion graph for the nanopub out of this
        nanopub_uri = 'http://purl.org/nanopub/temp/mynanopub'
        this_nanopub = rdflib.term.URIRef(nanopub_uri)
        this_step = rdflib.term.URIRef(nanopub_uri + '#step')

        NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
        
        PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
        PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")

        DUL = rdflib.Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
        BPMN = rdflib.Namespace("http://dkm.fbk.eu/index.php/BPMN2_Ontology#")

        PWO = rdflib.Namespace("http://purl.org/spar/pwo#")
        HYCL = rdflib.Namespace("http://purl.org/petapico/o/hycl#")

        rdf = rdflib.Graph()
        rdf.add( (this_step, DUL.isDescribedBy, this_nanopub) )
        rdf.add( (this_step, RDF.type, BPMN.manualTask) )
        rdf.add( (this_step, DC.description, rdflib.Literal(prefix + exact + suffix)) )

        # This creates the nanopub rdf (but does not publish it) so you can see it. Once you are ready to publish, change Nanopub.rdf to Nanopub.publish
        np_rdf = Nanopub.rdf(assertionrdf=rdf, uri=nanopub_uri, introduces_concept=this_step, derived_from=rdflib.term.URIRef(url))

        print(np_rdf.serialize(format='trig').decode('utf-8'))
