import json
import rdflib
from datetime import datetime
from rdflib.namespace import RDF, RDFS, DC, DCTERMS, XSD, OWL
from fairworkflows import Nanopub

# Read in the json file (exported from hypothesis)
with open('io.json') as infile:
    data = json.load(infile)

    # Loop through every annotation entry in the json
    entry = data['protocol']

    # Get whatever information you want for your manual step description
    doi = entry['doi']
    steps = entry['steps']
    creator = entry['creator'] ['username']

    # print(f'url={url}\nprefix={prefix}\nexact={exact}\nsuffix={suffix}\ntitle={title}')


    for step in steps :
        # Some standard ontologies used for nanopubs and describing workflows.
        NP = rdflib.Namespace("http://www.nanopub.org/nschema#")
        PPLAN = rdflib.Namespace("http://purl.org/net/p-plan#")
        PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
        DUL = rdflib.Namespace("http://ontologydesignpatterns.org/wiki/Ontology:DOLCE+DnS_Ultralite/")
        BPMN = rdflib.Namespace("https://www.omg.org/spec/BPMN/")
        PWO = rdflib.Namespace("http://purl.org/spar/pwo/")
        PAV = rdflib.Namespace("http://purl.org/pav/")
        RESEARCHER = rdflib.Namespace("https://www.protocols.io/researchers/")

        # Now make assertion graph for the nanopub out of this
        this_np = rdflib.Namespace(doi+'#')
        this_step = rdflib.term.URIRef(doi + '#step')
        np_rdf = rdflib.ConjunctiveGraph()
        head = rdflib.Graph(np_rdf.store, this_np.Head)
        assertion = rdflib.Graph(np_rdf.store, this_np.assertion)
        provenance = rdflib.Graph(np_rdf.store, this_np.provenance)
        pubInfo = rdflib.Graph(np_rdf.store, this_np.pubInfo)

        np_rdf.bind("", this_np)
        np_rdf.bind("np", NP)
        np_rdf.bind("p-plan", PPLAN)
        np_rdf.bind("prov", PROV)
        np_rdf.bind("dul", DUL)
        np_rdf.bind("bpmn", BPMN)
        np_rdf.bind("pwo", PWO)
        np_rdf.bind("dc", DC)
        np_rdf.bind("pav", PAV)
        np_rdf.bind("io", RESEARCHER)

        head.add((this_np[''], RDF.type, NP.Nanopublication))
        head.add((this_np[''], NP.hasAssertion, this_np.assertion))
        head.add((this_np[''], NP.hasProvenance, this_np.provenance))
        head.add((this_np[''], NP.hasPublicationInfo, this_np.pubInfo))
        
        creationtime = rdflib.Literal(datetime.now(),datatype=XSD.dateTime)
        pubInfo.add((this_np[''], Nanopub.PROV.wasAttributedTo, RESEARCHER.oxgiraldo))
        pubInfo.add((this_np[''], Nanopub.PROV.generatedAtTime, creationtime))

        components = step ['components']
        for component in components :
            if component ['title'] == 'description' :
                description = component ['source'] ['description'] 
                assertion.add( (this_step, RDF.type, BPMN.manualTask) )
                assertion.add( (this_step, DC.description, rdflib.Literal(description)) )


        provenance.add((this_np.assertion, PROV.wasDerivedFrom, rdflib.URIRef(doi))) 



        print(np_rdf.serialize(format='trig').decode('utf-8'))
