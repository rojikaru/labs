#include <bits/stdc++.h>
using namespace std;

constexpr char DIRTY = '*', CLEAN = '.';
const vector<pair<int, int>> directions{{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;

    vector<string> floor(n);
    vector<pair<int, int>> dirty_cells;
    for (int i = 0; i < n; ++i)
    {
        cin >> floor[i];
        for (int j = 0; j < m; ++j)
        {
            if (floor[i][j] != DIRTY)
                continue;
            dirty_cells.emplace_back(i, j);
        }
    }

    size_t k = dirty_cells.size();
    if (k == 0)
    {
        cout << 0;
        return 0;
    }

    vector<vector<int>> manhattan_dist(k, vector<int>(k, 0));
    for (size_t i = 0; i < k; ++i)
        for (size_t j = 0; j < k; ++j)
            manhattan_dist[i][j] = (
                abs(dirty_cells[i].first - dirty_cells[j].first) + 
                abs(dirty_cells[i].second - dirty_cells[j].second)
            );

    // Bitmask DP
    uint64_t FULL = 1 << k;

    // Minimal Hamiltonian Path (without returning to start)
    vector<int> dp((size_t)FULL * k, INT32_MAX);
    auto idx = [&k](size_t mask, int last) -> size_t {
        return mask * k + last;
    };

    // Base case: single node paths
    for (size_t i = 0; i < k; ++i) {
        dp[idx(1u << i, i)] = abs(dirty_cells[i].first) + abs(dirty_cells[i].second);
    }

    for (uint32_t mask = 1; mask < FULL; ++mask) {
        // iterate only bits set in mask
        uint32_t mm = mask;
        while (mm != 0) {
            int i = countr_zero(mm);    // get lowest set bit
            mm &= mm - 1;               // clear lowest set bit

            int current = dp[idx(mask, i)];
            if (current == INT32_MAX) continue;

            // iterate unvisited nodes only
            uint32_t remaining_bits = (FULL - 1u) & ~mask;
            while (remaining_bits != 0) {
                int j = countr_zero(remaining_bits);
                remaining_bits &= remaining_bits - 1;

                uint32_t new_mask = mask | (1u << j);
                int &dst = dp[idx(new_mask, j)];
                int candidate = current + manhattan_dist[i][j];
                if (candidate < dst) dst = candidate;
            }
        }
    }

    
    int bestMove = INT32_MAX;
    for (size_t i = 0; i < k; ++i) {
        int candidate = dp[idx(FULL - 1, i)];
        if (candidate < bestMove) bestMove = candidate;
    }

    const uint64_t answer = bestMove + k;
    cout << answer << '\n';

    return 0;
}
