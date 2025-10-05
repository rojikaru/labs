#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;

    vector<vector<int>> friends(n);
    for (int i = 0, x = 0, y = 0; i < m; i++) {
        cin >> x >> y;
        --x; --y;
        friends[x].push_back(y);
        friends[y].push_back(x);
    }

    vector<int> sicks(k);
    for (int i = 0; i < k; i++) {
        cin >> sicks[i];
        --sicks[i];
    }

    // Multi-source BFS
    vector visited(n, false);
    queue<int> q;
    for (int sick : sicks) {
        if (sick != 0 && !visited[sick]) {
            visited[sick] = true;
            q.push(sick);
        }
    }

    while (!q.empty()) {
        const int current = q.front(); q.pop();
        for (const int their_friend : friends[current]) {
            if (their_friend == 0) continue; // forbid node 0
            if (!visited[their_friend]) {
                visited[their_friend] = true;
                q.push(their_friend);
            }
        }
    }

    vector<int> result;
    for (const int my_friend : friends[0]) {
        if (visited[my_friend]) result.push_back(my_friend);
    }

    ranges::sort(result);
    result.erase(ranges::unique(result).begin(), result.end());

    cout << result.size() << '\n';
    for (const int i : result) {
        cout << i + 1 << ' ';
    }

    return 0;
}
