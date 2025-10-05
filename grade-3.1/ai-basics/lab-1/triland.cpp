#include <iostream>
#include <vector>
#include <set>
#include <map>
#include <queue>
using namespace std;

template <class T>
struct Coord {
    T x, y, z;
    auto operator<=>(const Coord &) const = default;
};

struct Triangle {
    Coord<int64_t> a, b, c;
    auto operator<=>(const Triangle &) const = default;
};

struct Edge {
    Coord<int64_t> a{}, b{};

    Edge(const Coord<int64_t> &a, const Coord<int64_t> &b) {
        this->a = a;
        this->b = b;

        if (this->a > this->b) {
            swap(this->a, this->b);
        }
    }

    auto operator<=>(const Edge &) const = default;
};

int64_t bfs(const vector<set<int64_t>> &arr, const int64_t start, const int64_t end) {
    queue<int64_t> q;
    q.push(start);

    vector<int64_t> dist(arr.size(), -1);
    dist[start] = 0;

    while (!q.empty()) {
        const int64_t current = q.front();
        q.pop();

        if (current == end) {
            return dist[current];
        }

        for (const auto &neighbor : arr[current]) {
            if (dist[neighbor] == -1) {
                dist[neighbor] = dist[current] + 1;
                q.push(neighbor);
            }
        }
    }

    return -1;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int64_t n, start, end;
    cin >> n >> start >> end;
    start--, end--;

    vector<Triangle> sectors(n);
    for (auto&[a, b, c] : sectors) {
        cin >> a.x >> a.y >> a.z
            >> b.x >> b.y >> b.z
            >> c.x >> c.y >> c.z;
    }

    // Create an edge mapping to sector indices
    map<Edge, set<int64_t>> edge_to_sectors;

    for (int64_t idx = 0; idx < n; ++idx) {
        const auto &[a, b, c] = sectors[idx];
        for (const auto &pair: {Edge(a, b), Edge(b, c), Edge(c, a)}) {
            edge_to_sectors[pair].insert(idx);
        }
    }

    vector<set<int64_t>> adj_list(n);
    for (const auto &[_, sector_indices]: edge_to_sectors) {
        if (sector_indices.size() <= 1) {
            continue;
        }
        for (const auto &u: sector_indices) {
            for (const auto &v: sector_indices) {
                if (u != v) {
                    adj_list[u].insert(v);
                }
            }
        }
    }

    cout << bfs(adj_list, start, end) << '\n';

    return 0;
}
