

import datetime
import numpy as np
import pandas as pd

# This will lead to a prime -> guigmatic-requirements building utility
# overview is given on
# https://github.com/baskaufs/tdwg-standards/blob/master/files-to-generate-from-prime-csv.txt

def create_term_terms(versions, isdefined_category):
    """Create the ./terms/term.csv file based on the prime file"

    pure prototyping ;-)

    Compare to original of
    https://github.com/baskaufs/tdwg-standards/blob/master/terms/terms.csv

    from pandas.util.testing import assert_frame_equal
    assert_frame_equal(term_terms_csv_cmp, ref_terms_cmp)
    """

    versions["issued"] = pd.to_datetime(versions["issued"])

    versions[["term_isDefinedBy", "term_localName"]] = versions["term_iri"].str.extract("(.*/)([^/]*$)", expand=True)
    versions_sub = versions[versions["term_isDefinedBy"] == isdefined_category].copy()

    term_agg = versions_sub.groupby("term_iri").apply(lambda x: x.sort_values("issued"))
    term_terms = term_agg.groupby(level=0, group_keys=False).agg({"issued": ['min', 'max'], 'status': 'last',
                                                              'replaces': 'first', 'rdf_type': 'last',
                                                              'definition': 'last', 'label': 'last',
                                                              'term_isDefinedBy': 'last', 'term_localName': 'last'})

    # Provide the naming of the columns
    term_terms.columns = [' '.join(col).strip() for col in term_terms.columns.values]
    term_terms.rename(columns={'term_isDefinedBy last' : 'term_isDefinedBy',
                               'label last' : 'label',
                               'status last' : 'status',
                               'rdf_type last' : 'rdf_type',
                               'replaces first' : 'replaces_term',
                               'issued min' : 'term_created',
                               'issued max' : 'term_modified',
                               'term_localName last' : 'term_localName',
                               'definition last' : 'rdfs_comment'}, inplace=True)
    term_terms = term_terms.reset_index()

    term_terms["term_deprecated"] = np.where(term_terms['status'] == "deprecated", 'True', np.nan)
    term_terms["document_modified"] = datetime.datetime.utcnow()

    replaces_term_temp = term_terms["replaces_term"].str.split("|", expand=True)
    replaces_term_temp[replaces_term_temp.isnull()] = np.nan
    replaces_term_temp.columns = ["replaces_term"] + ["replaces" + str(j) + "_term" for j in range(1, replaces_term_temp.shape[1])]
    if len(replaces_term_temp.columns) > 2:
        raise Exception("Such a high number of replaced fields is not supported by The Guid-o-Matic, contact Steve ;-)")
    if len(replaces_term_temp.columns) <= 2:
        replaces_term_temp["replaces2_term"] = np.nan

    # get rid of date-ends in the `replace_terms`
    replaces_term_temp = replaces_term_temp.replace({"-([0-9]{4}-[0-9]{2}-[0-9]{2})$" :  ""},
                                                    regex=True)

    term_terms = term_terms.drop(["term_iri", "status", "replaces_term"], axis=1)
    term_terms = pd.concat([term_terms, replaces_term_temp], axis=1)

    return term_terms

versions = pd.read_csv(term_versions_file)
isdefined_category = "http://rs.tdwg.org/dwc/terms/"
term_terms_csv = create_term_terms(versions, isdefined_category)
term_terms_csv.head()
