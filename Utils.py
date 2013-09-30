'''
The MIT License (MIT)

Copyright (c) 2013 wilko.henecka@adelaide.edu.au

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import networkx as nx


def printGraphStatistics(graphfile, outfile):
    G = nx.read_gml(graphfile)
    stats = {}
    stats['numberOfNodes'] = G.number_of_nodes()
    stats['numberOfEdges'] = G.number_of_edges()
    stats['averageShortestPathLength'] = nx.average_shortest_path_length(G)
    l = [max(x.values()) for x in nx.all_pairs_shortest_path_length(G).values()]
    stats['maxShortestPathLength'] = max(l)
    l = nx.degree(G).values()
    stats['averageNodeDegree'] = float(sum(l))/len(l)
    stats['maximumNodDegree'] = max(l)
    #stats['averagePathLength'] = computeAveragePathLength(G)
    #d = computeNumberOfPathsOfLengthK4(G)
    #stats['numberOfPathsOfLengthK'] = d
    #stats['averageNumberOfHops'] = computeAverageNumberOfHopsForAllSimplePaths2(d)
    gsf = open(outfile, 'w')
    gsf.write('Statistics for graph: %s\n' % (graphfile))
    gsf.write('------------------------------------------\n')
    for k,v in stats.items():
        gsf.write( '%s: %s\n' % (k,str(v)))
    gsf.write('------------------------------------------\n')
    gsf.close()
    
def pathLength(path, G):
    length = 0
    s = path[0]
    for d in path[1:]:
        length += G.edge[s][d]['weight']
        s = d
    return length
      
def computeAveragePathLength(G):
    pathCount = 0
    pathSum = 0
    for snode in G.nodes_iter():
        for dnode in G.nodes_iter():
            if snode == dnode:
                continue
            print 's:%s d%s' %(snode, dnode)
            for path in nx.all_simple_paths(G, source=snode, target=dnode):
                pathCount += 1
                pathSum += pathLength(path,G)
    return pathSum/float(pathCount)

def computeAverageNumberOfHopsForAllSimplePaths(G):
    ''' this is quite slow ... Better use computeNumberOfPathsOfLengthK'''
    pathCount = 0
    hopSum = 0
    for snode in G.nodes_iter():
        for dnode in G.nodes_iter():
            if snode == dnode:
                continue
            print 's:%s d%s' %(snode, dnode)
            for path in nx.all_simple_paths(G, source=snode, target=dnode):
                pathCount += 1
                hopSum += len(path)
    return hopSum/float(pathCount)

def computeAverageNumberOfHopsForAllSimplePaths2(dictOfKSums):
    sum = 0
    div = 0
    for key in dictOfKSums.keys():
        sum += key*dictOfKSums[key]
        div += dictOfKSums[key]
    return sum/float(div)

def computeNumberOfPathsOfLengthK(G):
    print 'Computing number of paths of length k for k=1 to number_of_nodes. This might take a while...'
    paths = set()
    for e in G.edges_iter():
        paths.add(e)
    result = {}
    result[1] = G.number_of_edges()
    newPaths = set()
    length = 2
    while len(paths) > 0:
        for path in paths:
            for neighb in nx.all_neighbors(G, path[0]):
                if neighb not in path:
                    if neighb < path[-1]:
                        newPaths.add((neighb,)+path)
                    else:
                        newPaths.add( ((neighb,)+path)[::-1] )
            for neighb in nx.all_neighbors(G, path[-1]):
                if neighb not in path:
                    if neighb < path[0]:
                        newPaths.add( (path + (neighb,))[::-1] )
                    else:
                        newPaths.add(path + (neighb,))
                    
        result[length] = len(newPaths)
        length += 1
        paths = newPaths
        newPaths = set()
    return result
    
    
def computeNumberOfPathsOfLengthK2(G):
    ''' second try ... '''
    results = {}
    for i in range(G.number_of_nodes()):
        results[i+1] = 0
    nn = G.number_of_nodes()
    nc = 1
    for node in G.nodes_iter():
        #print 'starting from node %s' %(str(node))
        neighb = nx.all_neighbors(G, node)
        for n in neighb:
            #print 'exploring node %s' %(str(n))
            explore(n, [node], G, results)
        print 'done %d of %d' % (nc, nn)
        nc += 1
    for k, v in results.iteritems():
        results[k] = v/2
    return results

def explore(node, visited, G, results):
    visited.append(node)
    results[len(visited)-1] += 1
    neighbours = nx.all_neighbors(G, node)
    avail = []
    for n in neighbours:
        if not n in visited:
            avail.append(n)
    for n in avail:
        explore(n, visited, G, results)
    visited.pop()


def computeNumberOfPathsOfLengthK4(G):
    ''' forths try ... '''
    results = {}
    for i in range(G.number_of_nodes()):
        results[i+1] = 0
    neighbourhood = {}
    for node in G.nodes_iter():
        hood = []
        for n in nx.all_neighbors(G, node):
            hood.append(n)
        neighbourhood[node] = hood
        
    nn = G.number_of_nodes()
    nc = 1
    for node in G.nodes_iter():
        #print 'starting from node %s' %(str(node))
        for n in neighbourhood[node]:
            #print 'exploring node %s' %(str(n))
            explore4(n, [node], G, results, neighbourhood)
        print 'done %d of %d' % (nc, nn)
        nc += 1
    for k, v in results.iteritems():
        results[k] = v/2
    return results

def explore4(node, visited, G, results, neighbourhood):
    visited.append(node)
    results[len(visited)-1] += 1
    #neighbours = nx.all_neighbors(G, node)
    avail = []
    for n in neighbourhood[node]:
        if not n in visited:
            avail.append(n)
    for n in avail:
        explore4(n, visited, G, results, neighbourhood)
    visited.pop()

def computeNumberOfPathsOfLengthK3(G):
    ''' this might take a while'''
    results = {}
    for i in range(G.number_of_nodes()):
        results[i+1] = 0
    for snode in G.nodes_iter():
        for dnode in G.nodes_iter():
            if snode == dnode:
                continue
            print 's:%s d%s' %(snode, dnode)
            for path in nx.all_simple_paths(G, source=snode, target=dnode):
                results[len(path)-1] += 1            
    for k, v in results.iteritems():
        results[k] = v/2
    return results

if __name__ == '__main__':
       
    G = nx.read_gml('barabasi_100_2.gml')
    printGraphStatistics('barabasi_100_2.gml', 'test.txt')
