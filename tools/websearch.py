from ddgs import DDGS

class WebSearch:
    def __init__(self, query):
        self.query = query  
    
    def search(self):
        result = None
        with DDGS() as ddgs:
            result = ddgs.text(self.query, max_results=5)
        if result is None:
            return []
        return result
    
def webSearch(query):
    """This tool is capable of fetching real-time data in the world.
    Args:
    query (str): The keyword/query to be searched
    """
    print(f"Searching the web: {query}")
    search = WebSearch(query)
    result = search.search()
    return result
    