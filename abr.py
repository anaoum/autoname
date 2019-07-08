import re
import logging

import zeep

class ABRClient:
    wsdl = "http://abr.business.gov.au/ABRXMLSearch/AbrXmlSearch.asmx?WSDL"
    abn_cache = {}
    def __init__(self, guid):
        self.client = zeep.Client(self.wsdl)
        self.guid = guid
        self.logger = logging.getLogger(type(self).__name__)
    def lookup_name(self, abn):
        if abn in self.abn_cache:
            return self.abn_cache[abn]
        result = self.client.service.ABRSearchByABN(abn, "Y", self.guid)
        response = result["response"]
        if "exception" in response and response["exception"] is not None:
            self.logger.warning("Could not lookup ABN. Exception occured: %s.", 
                    response["exception"]["exceptionDescription"])
            return None
        try:
            business_entity = response["businessEntity"]
            if business_entity["mainTradingName"]:
                name = business_entity["mainTradingName"][0]["organisationName"]
            else:
                name = business_entity["_value_1"][0]["mainName"]["organisationName"]
            self.abn_cache[abn] = name
            return name
        except (TypeError, KeyError, IndexError) as e:
            self.logger.warning("Could not parse response from ABR. " \
                    "Exception occured: %s.", e)
            return None
    @staticmethod
    def remove_suffixes(name):
        old = None
        while name != old:
            old = name
            name = re.sub(" PROPRIETARY$", "", name, flags=re.I)
            name = re.sub(" P\.?T\.?Y\.?$", "", name, flags=re.I)
            name = re.sub(" LIMITED$", "", name, flags=re.I)
            name = re.sub(" L\.?T\.?D\.?$", "", name, flags=re.I)
        return name
