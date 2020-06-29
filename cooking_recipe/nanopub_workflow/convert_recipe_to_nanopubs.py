import sys
import rdflib
from urllib.parse import urlsplit, urlunsplit

from fairworkflows import Nanopub

def purlify_uri(uriref: rdflib.term.URIRef, fragment='') -> rdflib.term.URIRef:
    """
    For the nanopub hashing/signing to work properly, the workflow or step should have a purl.org URI
    (not plex.org etc). This function converts the URI to a purl.org base, with optional fragment.
    """

    _, _, path, _, _ = urlsplit(uriref)

    new_path = '/nanopub/temp' + path
    purluri = urlunsplit((
                            'http',
                            'purl.org',
                            new_path,
                            '',
                            fragment
                        ))

    return rdflib.term.URIRef(purluri)


def get_plan(np_rdf):
    rdf_type = rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    pplan_plan = rdflib.term.URIRef('http://purl.org/net/p-plan#Plan')
    description = rdflib.term.URIRef('http://purl.org/dc/terms/description')

    qres = np_rdf.query(
     """SELECT DISTINCT ?planURI ?planDescription
        WHERE {
           ?planURI ?type ?pplan ;
                    ?description ?planDescription .
        }""",
        initBindings={'type': rdf_type, 'pplan': pplan_plan, 'description': description})

    triples = []
    workflow_uri = None
    for row in qres:
        workflow_uri = purlify_uri(row['planURI'], fragment='workflow')
        triples.append((workflow_uri, rdf_type, pplan_plan))
        triples.append((workflow_uri, description, row['planDescription']))

    if len(triples) == 0:
        return None, None

    return str(workflow_uri), workflow_uri, triples


def get_first_step_triple(np_rdf):
    hasFirstStep = rdflib.term.URIRef('http://purl.org/spar/pwo#hasFirstStep')
    qres = np_rdf.query(
     """SELECT DISTINCT ?planURI ?firstStepURI
        WHERE {
           ?planURI ?hasFirstStep ?firstStepURI .
        }""",
        initBindings={'hasFirstStep': hasFirstStep})

    triples = []
    for row in qres:
        firstStepURI = purlify_uri(row['firstStepURI'], fragment='step')
        workflow_uri = purlify_uri(row['planURI'], fragment='workflow')
        triples.append((workflow_uri, hasFirstStep, firstStepURI))

    if len(triples) == 0:
        return None
    elif len(triples) > 1:
        sys.exit("Warning: More than one first step declared.")

    return triples[0]


def get_plex_steps(np_rdf):
    rdf_type = rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    manualTask = rdflib.term.URIRef('http://dkm.fbk.eu/index.php/BPMN2_Ontology#ManualTask')
    scriptTask = rdflib.term.URIRef('http://dkm.fbk.eu/index.php/BPMN2_Ontology#ScriptTask')
    description = rdflib.term.URIRef('http://purl.org/dc/terms/description')
    pplan_step = rdflib.term.URIRef('http://purl.org/net/p-plan#Step')

    initBindings = {'type': rdf_type, 'manualTask': manualTask, 'scriptTask': scriptTask, 'description': description}
    qres = np_rdf.query(
     """SELECT DISTINCT ?stepURI ?task ?taskDescription
        WHERE {
            ?stepURI ?type ?task .
            FILTER ( ?task = ?manualTask || ?task = ?scriptTask )
            OPTIONAL { ?stepURI ?description ?taskDescription }
        }""", initBindings=initBindings)

    steps = {}
    for row in qres:
        step = []

        stepURI = purlify_uri(row['stepURI'], fragment='step')

        step.append((stepURI, rdf_type, row['task']))
        step.append((stepURI, description, row['taskDescription']))
        step.append((stepURI, rdf_type, pplan_step))

        # Add step triples to dict, with the URI as the key
        uri_str = str(stepURI)
        steps[uri_str] = {'triples': step, 'rdfterm': stepURI}

    return steps


def get_plex_topology(np_rdf):
    precedes = rdflib.term.URIRef('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#precedes')
    qres = np_rdf.query(
     """SELECT DISTINCT ?stepBefore ?stepAfter 
        WHERE {
           ?stepBefore ?precedes ?stepAfter .
        }""",
        initBindings={'precedes': precedes})

    topology = []
    for row in qres:
        stepBefore = purlify_uri(row['stepBefore'], fragment='step')
        stepAfter = purlify_uri(row['stepAfter'], fragment='step')
        topology.append((stepBefore, precedes, stepAfter))
    return topology


# Parse the combined workflow/step rdf into an rdflib graph
rdf = rdflib.Graph()
rdf.parse('../rdf/cooking_recipe_instructions.nt', format='nt')

# Get triples for this plan (its type, and its description)
plan_uri, plan_rdfterm, plan_triples = get_plan(rdf)
if plan_triples:
    print('\nPlan:')
    for triple in plan_triples:
        print(triple)
else:
    sys.exit('Plan triples not present (need both type and description)')

# Get triple indentifying first step
first_step_triple = get_first_step_triple(rdf)
if first_step_triple:
    print('\nFirst step:\n', first_step_triple)
else:
    sys.exit('No first step specified')


# Get the triples describing each individual step
steps = get_plex_steps(rdf)
print('\nSteps:')
for step_uri, step_triples in steps.items():
    print('\nStep', step_uri)
    for triple in step_triples:
        print(triple)

# Get the topology of the workflow (which steps follow each other)
topology = get_plex_topology(rdf)
print('\nTopology:')
for triple in topology:
    print(triple)



# Publish the steps individually
uri_map = {}
for step_uri, step_info in steps.items():

    # Publish the triples for this step as a nanopub
    step_rdf = rdflib.Graph()
    for triple in step_info['triples']:
        step_rdf.add(triple)

#    print(Nanopub.rdf(step_rdf, uri=step_uri, introduces_concept=step_info['rdfterm']).serialize(format='trig').decode('utf-8'))
    published_URI = Nanopub.publish(step_rdf, uri=step_uri, introduces_concept=step_info['rdfterm'])

    print(published_URI)

    # Publishing the step as a nanopub strips the fragment from it, so add that back in...
    published_URI += '#step'

    # Build mapping of URIs so the workflow nanopub uses the published URIs
    uri_map[step_uri] = rdflib.term.URIRef(published_URI)

print('Mapping of step URIs to published URIs:')
print(uri_map)

# Now construct the workflow rdf itself
workflow_rdf = rdflib.Graph()

# Type and description
for triple in plan_triples:
    workflow_rdf.add(triple)

# First step
workflow_rdf.add(first_step_triple)

# Topology
for triple in topology:
    workflow_rdf.add(triple)

# Map the step URIs to their published form
new_workflow_rdf = rdflib.Graph()
for subj, pred, obj in workflow_rdf:
    subj = uri_map.get(str(subj), subj)
    obj = uri_map.get(str(obj), obj)
    new_workflow_rdf.add( (subj, pred, obj) )
workflow_rdf = new_workflow_rdf

# Publish this workflow
workflow_URI = Nanopub.publish(workflow_rdf, uri=plan_uri, introduces_concept=plan_rdfterm)
print('Workflow published at', workflow_URI)
