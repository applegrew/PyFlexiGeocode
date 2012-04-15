
"""
Geocode test code.

License: GPL version 3
"""

from pyavltree import Node

SEPERATOR = ','

class PoolNode(Node):

    """
    This represents a leaf, data carring node.

    Typically this should carry the latitude, longitude or other
    geo info. The `address` and `name` are required.

    address -- This is a list with the cuurent location's address. The bigger
        enclosing area being at the top.
    name -- This the name of the location. This is used as the key value while
        searching for a node. This implementation does an exact match.
    """

    def __init__(self, name, address=[]):
        super(PoolNode, self).__init__(name)
        self.address = address
        self.name = name

    def __str__(self):
        address = self.full_address()
        address.reverse()
        return '"' + SEPERATOR.join(address) + '"'

    def full_address(self):
        return self.address + [self.name]

class ResultNode(object):

    """
    Each instance of this contains one result.

    address -- This is a list of the location's address. Like PoolNode, this list to
        is inverted, but unlike it, it includes the cuurent node name (at the list's end).
    node -- Refers to PoolNode instance of this node. PoolNode instances MUST be considered
        readonly. PoolNode is a data node, so it is not instantiated for every query.
    rank -- A number which denotes how well matched the result is with the query. Lesser the value
        the better being the match. 0 being exact match.
    """

    address = []
    node = None
    rank = 0

    def __init__(self, node=None, address=None, rank=0):
        self.node = node
        if (address is None) and (not node is None):
            self.address = node.full_address()
        else:
            self.address = address

        self.rank = rank

    def str_address(self):
        address = [] + self.address
        address.reverse()
        return SEPERATOR.join(address)

    def __str__(self):
        if self.node is None:
            tag = 'NoResult:'
        else:
            tag = 'Result:'
        return '"%s %s (%d)"' % (tag, self.str_address(), self.rank)

    def add_parent_address(self, parent_address):
        if parent_address:
            self.address.insert(0, parent_address)

class SearchSlice(object):

    """
    Represents a 'slice' in address hierarchy.

    An example search hierarchy can be 'Home No., District, State, Country'. SearchPool maitains a
    'pool' of PoolNode and searches through all of them for matching address. It doesn't have the provision
    to partition the search space. The user may provide Country and State and they can help in reducing the
    sample space by quite a bit. SearchSlice is the way to make this partitioning of the search space.

    So we can design a hierarchy where Country and State are 'slices' each. Each State 'slice' can then point
    to a SearchPool instead. One SearchSlice instance can span only one level. So, one instance of this cannot
    handel both Country and State; we need two.
    """

    def __init__(self, data, node):
        """
        Constructor.

        data -- Is a map from location name to a instance of SearchPool or SearchSlice
        node -- Instance of PoolNode for the current node. This will hold the lat, lon, etc. geo data for this node.
        """
        self.data = data
        self.node = node

    def locate(self, query, return_empty=False, limit=-1):
        """
        Public method. Use this to trigger the search.

        query -- This is a list. e.g. ['US', 'New York', 'Pearl Street']
        return_empty -- If this is True the empty ResultNode too would returned. Helpful to trace the search paths
        limit -- Max no. of results. Onus of enforcing this limit is on the backing search tree (in SearchPool).
            Its primary purpose is to avoid DOS attack by seartching for something with too many results.
        """
        query_address = query[0:1]
        query_name = query_address[0]
        pool = self._search(query_name, query_address)
        lc = limit
        if pool:
            query = query[1:]
            if len(query) == 0:
                # Nothing more to query.
                res = [ResultNode(pool.node, rank=0)]
            else:
                # Partial result match found. Now time to dip inside its pool/slice.
                res = pool.locate(query, return_empty, lc)
                if limit != -1:
                    lc = lc - len(res)
        else: # No match found. We need to dip in all pools now!
            res = []
            for key in self.data:
                r = self.data[key].locate(query, return_empty, lc) # Sending full query.
                if r:
                    res = res + r
                    if limit != -1:
                        lc = lc - len(r)
                        if lc <= 0:
                            break

        if res or return_empty:
            for rn in res:
                rn.add_parent_address(self.node.name) # Prepedning cuurent name to children ResultNodes' addresses.
            return res
        else:
            return []
            
    def _search(self, query_name, query_address):
        # Here we use Python.dict as data structure.

        # This can have any implementation. It can use any kind of search algo. Here we use hashtable.
        if self.data:
            if self.data.has_key(query_name):
                return self.data[query_name]
            else:
                return None
        return None


class SearchPool(object):

    """
    Represents a 'pool' of unpartitioned data.

    All will be searched for matching address. Each node in this
    has its complete address, in this pool's context.
    """
    
    def __init__(self, data, node):
        """
        Constructor.

        data -- Is a map from location name to a instance of SearchPool or SearchSlice
        node -- Instance of PoolNode for the current node. This will hold the lat, lon, etc. geo data for this node.
        """
        self.data = data
        self.node = node # This is the data structure which holds the data for this node, e.g. lat, lon, etc.

    def locate(self, query, return_empty=False, limit=-1):
        """
        Public method. Use this to trigger the search.

        query -- This is a list. e.g. ['US', 'New York', 'Pearl Street']
        return_empty -- If this is True the empty ResultNode too would returned. Helpful to trace the search paths
        limit -- Max no. of results. Onus of enforcing this limit is on the backing search tree (in SearchPool).
            Its primary purpose is to avoid DOS attack by seartching for something with too many results.
        """
        query_address = query[:-1] # Address won't have the query_name part
        query_name = query[-1]

        res = self._search(query_name, query_address, limit)
        if not res and return_empty:
            return [ResultNode(address=[self.node.name])] # An empty no result node
        else:
            return res

    def _search(self, query_name, query_address, limit):
        # This can have any implementation. It can use any kind of search algo. Here we use AVL tree.

        if self.data:
            #print '>>>' + query_address
            nodes = self.data.find(query_name, limit) # We pass the limit as-is. It is upto to the backing algo to honour it.
            if nodes:
                n = []
                for node in nodes:
                    r = ResultNode(node)
                    r.add_parent_address(self.node.name)
                    n.append(r)
                return n

        return []


def _lcs_diff_cent(s1, s2):
    """
    Calculates Longest Common Subsequence Count Difference in percentage between two strings or lists.

    LCS reference: http://en.wikipedia.org/wiki/Longest_common_subsequence_problem.
    Returns an integer from 0-100. 0 means that `s1` and `s2` have 0% difference, i.e. they are same.
    """
    m = len(s1)
    n = len(s2)

    if s1 == s2:
        return 0
    if m == 0: # When user given query is empty then that is like '*'' (match all)
        return 0
    if n == 0:
        return 100

    matrix = [[0] * (n + 1)] * (m + 1)
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                matrix[i][j] = matrix[i-1][j-1] + 1
            else:
                matrix[i][j] = max(matrix[i][j-1], matrix[i-1][j])

    return int( ( 1 - float(matrix[m][n]) / m ) * 100 )

def post_process_result(res, query, max_rank=None):
    """
    Can be used to process the results returned by `loate()`.

    This first ranks the result retunred by comparing them with the query, then it sorts it
    accoriding to the rank. The best matches are at the top.

    query -- This is a list. e.g. ['US', 'New York', 'Pearl Street']
    max_rank -- If this is set, then all results with rank greater than this value are dropped. This can help
        in sight optimisation as the dropped results won't take part in rank-wise sorting.
    """
    # Sets the rank of result
    i = 0
    for r in res:
        r.rank = _lcs_diff_cent(query, r.address)
        if not max_rank is None and r.rank > max_rank:
            res.pop(i)
        else:
            i = i + 1

    # It sorts the result in ascending order of rank
    res.sort(lambda a,b: a.rank-b.rank)

    return res

