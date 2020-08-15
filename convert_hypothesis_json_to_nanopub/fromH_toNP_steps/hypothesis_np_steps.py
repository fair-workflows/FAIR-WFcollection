import json
import rdflib
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, XSD, OWL
from fairworkflows import Nanopub

# Read in the json file (exported from hypothesis)
with open('annotation_steps_publicGroup.json') as infile:
    data = json.load(infile)

    # Loop through every annotation entry in the json
    for entry in data:

        # Get whatever information you want for your manual step description
        url = entry['url']
        user = entry['user']
        exact = entry['exact']
        created = entry['created']
        id = entry['id']
        title = entry['title']

        # print(f'url={url}\nprefix={prefix}\nexact={exact}\nsuffix={suffix}\ntitle={title}')


        # Some standard ontologies used for nanopubs and describing workflows.
        NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
        PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
        PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
        DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
        BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
        PWO = rdflib.Namespace("http://purl.org/spar/pwo/")
        AUT = rdflib.Namespace("https://hypothes.is/a/")

        # Now make assertion graph for the nanopub out of this
        this_np = rdflib.Namespace(url+'#')
        this_step = rdflib.term.URIRef(url + '#step')
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, this_np.Head)
        assertion = rdflib.Graph(np_rdf.store, this_np.assertion)
        provenance = rdflib.Graph(np_rdf.store, this_np.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, this_np.pubInfo)

        np_rdf.bind("", this_np)
        np_rdf.bind("np", NP)
        np_rdf.bind("p-plan", PPLAN)
        np_rdf.bind("authority", AUT)
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)
        np_rdf.bind("dc", DC)

        head.add((this_np[''], RDF.type, NP.Nanopublication))
        head.add((this_np[''], NP.hasAssertion, this_np.assertion))
        head.add((this_np[''], NP.hasProvenance, this_np.provenance))
        head.add((this_np[''], NP.hasPublicationInfo, this_np.pubInfo))

        
        assertion.add( (this_step, RDF.type, BPMN.manualTask) )
        assertion.add( (this_step, DC.description, rdflib.Literal(exact)) )

        creationtime = rdflib.Literal(created, datatype=XSD.dateTime)
        provenance.add((this_np.assertion, PROV.generatedAtTime, creationtime))
        provenance.add((this_np.assertion, PROV.wasDerivedFrom, rdflib.URIRef("https://hypothes.is/a/"+id))) 

        pubInfo.add((this_np[''], PROV.wasAttributedTo, AUT[user]))
        pubInfo.add((this_np[''], PROV.generatedAtTime, creationtime))


        print(np_rdf.serialize(format='trig').decode('utf-8'))
