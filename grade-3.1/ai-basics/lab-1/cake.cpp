#include <bits/stdc++.h>
using namespace std;

constexpr int MIN_LEN = 1, MAX_LEN = 200;
constexpr int INF = INT32_MAX;

struct Edge
{
    int u, v, w;
    bool is_variable;
};

auto dijkstra(const vector<Edge> &edges, int n, int src)
{
    vector<int> distances(n, INF);
    vector<int> parents(n, -1);
    distances[src] = 0;
    
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
    pq.push({0, src});
    
    while (!pq.empty())
    {
        const auto [d, u] = pq.top();
        pq.pop();
        
        if (d > distances[u])
            continue;
        
        for (int i = 0; i < edges.size(); i++)
        {
            const auto &e = edges[i];
            int v = -1;
            if (e.u == u)
                v = e.v;
            else if (e.v == u)
                v = e.u;
            else
                continue;
            
            if (e.w > 0 && distances[u] + e.w < distances[v])
            {
                distances[v] = distances[u] + e.w;
                parents[v] = i;
                pq.push({distances[v], v});
            }
        }
    }
    
    return pair{distances, parents};
}

int edge_to_increase(const vector<Edge>& edges, const vector<int>& parents, int dst) {
    while (dst != 0) {
        int eid = parents[dst];
        if (eid == -1)
            break;
        
        if (edges[eid].is_variable)
            return eid;
        
        dst = (edges[eid].u == dst) ? edges[eid].v : edges[eid].u;
    }
    return -1;
}

int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    int n, m, target;
    cin >> n >> m >> target;
    
    vector<Edge> edges(m);
    for (int i = 0; i < m; i++)
    {
        cin >> edges[i].u >> edges[i].v >> edges[i].w;
        edges[i].u--;
        edges[i].v--;
        edges[i].is_variable = (edges[i].w == -1);
        
        if (edges[i].is_variable)
            edges[i].w = MIN_LEN;
    }
    
    while (true)
    {
        const auto [distances, parents] = dijkstra(edges, n, 0);
        int dist = distances[n - 1];
        
        if (dist == target)
        {
            for (auto &e : edges)
                cout << e.w << '\n';
            return 0;
        }
        
        if (dist > target)
            break;
        
        // Reconstruct path and find variable edge to increase
        int target_edge = edge_to_increase(edges, parents, n - 1);
        if (target_edge == -1)
            break;

        // The minimum needed to reach target or max possible
        int increase = min(target - dist, MAX_LEN - edges[target_edge].w);
        edges[target_edge].w += increase;
    }
    
    cout << "-1\n";
    return 0;
}
