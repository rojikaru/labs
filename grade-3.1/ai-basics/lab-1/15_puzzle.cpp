#include <bits/stdc++.h>
using namespace std;

constexpr int PROBLEM_SIZE = 3;
constexpr int TOTAL_TILES = PROBLEM_SIZE * PROBLEM_SIZE;
constexpr int LAST_POS = PROBLEM_SIZE - 1;

using Matrix = array<array<int8_t, PROBLEM_SIZE>, PROBLEM_SIZE>;

struct State
{
    Matrix matrix;
    int8_t zero_x, zero_y;

    auto operator<=>(const State &other) const = default;
};

struct StateHash
{
    size_t operator()(const State &s) const
    {
        size_t h = 0;
        for (int y = 0; y < PROBLEM_SIZE; ++y)
            for (int x = 0; x < PROBLEM_SIZE; ++x)
                h = h * 10 + s.matrix[y][x];
        return h;
    }
};

struct PQNode
{
    State state;
    int f_score;

    bool operator>(const PQNode &other) const
    {
        return f_score > other.f_score;
    }
};

constexpr array<pair<int, int>, 4> directions = {{{0, 1}, {1, 0}, {0, -1}, {-1, 0}}};

inline bool check_bound(int x, int y)
{
    return x >= 0 && x < PROBLEM_SIZE && y >= 0 && y < PROBLEM_SIZE;
}

// Precompute goal positions for each tile
constexpr array<pair<int, int>, TOTAL_TILES> goal_positions = []()
{
    array<pair<int, int>, TOTAL_TILES> pos{};
    for (int i = 1; i < TOTAL_TILES; ++i)
    {
        pos[i] = {(i - 1) % PROBLEM_SIZE, (i - 1) / PROBLEM_SIZE};
    }
    pos[0] = {LAST_POS, LAST_POS};
    return pos;
}();

int heuristics(const State &state)
{
    int distance = 0;

    // Manhattan distance
    for (int y = 0; y < PROBLEM_SIZE; ++y)
    {
        for (int x = 0; x < PROBLEM_SIZE; ++x)
        {
            int val = state.matrix[y][x];
            if (val == 0)
                continue;
            auto [goalX, goalY] = goal_positions[val];
            distance += abs(x - goalX) + abs(y - goalY);
        }
    }

    // Linear conflict
    // Checks for each pair of tiles in the same row if they are in their goal row
    // and if they are reversed in order compared to their goal positions.
    for (int y = 0; y < PROBLEM_SIZE; ++y)
    {
        for (int x1 = 0; x1 < PROBLEM_SIZE; ++x1)
        {
            int t1 = state.matrix[y][x1];
            if (!t1 || goal_positions[t1].second != y)
                continue;

            for (int x2 = x1 + 1; x2 < PROBLEM_SIZE; ++x2)
            {
                int t2 = state.matrix[y][x2];
                if (t2 && goal_positions[t2].second == y &&
                    goal_positions[t1].first > goal_positions[t2].first)
                    distance += 2;
            }
        }
    }

    return distance;
}

optional<int> a_star(State start, const State &end)
{
    priority_queue<PQNode, vector<PQNode>, greater<PQNode>> pq;
    unordered_map<State, int, StateHash> g_score;

    g_score[start] = 0;
    pq.push({start, heuristics(start)});

    while (!pq.empty())
    {
        auto [current, f] = pq.top();
        pq.pop();

        int current_g = g_score[current];

        // Skip if outdated
        if (f > current_g + heuristics(current))
            continue;

        if (current == end)
            return current_g;

        for (auto [dx, dy] : directions)
        {
            int new_x = current.zero_x + dx;
            int new_y = current.zero_y + dy;

            if (!check_bound(new_x, new_y))
                continue;

            State neighbor = current;
            swap(neighbor.matrix[current.zero_y][current.zero_x],
                 neighbor.matrix[new_y][new_x]);
            neighbor.zero_x = new_x;
            neighbor.zero_y = new_y;

            int tentative_g = current_g + 1;

            auto it = g_score.find(neighbor);
            if (it == g_score.end() || tentative_g < it->second)
            {
                g_score[neighbor] = tentative_g;
                pq.push({neighbor, tentative_g + heuristics(neighbor)});
            }
        }
    }

    return nullopt;
}

int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    Matrix matrix{};
    string line;
    int8_t zero_x, zero_y;

    for (int y = 0; y < PROBLEM_SIZE; ++y)
    {
        getline(cin, line);
        for (int x = 0; x < PROBLEM_SIZE; ++x)
        {
            matrix[y][x] = line[x] - '0';
            if (matrix[y][x] == 0)
            {
                zero_x = x;
                zero_y = y;
            }
        }
    }

    State current_state{matrix, zero_x, zero_y};

    Matrix terminal_matrix{};
    for (int y = 0, i = 0; y < PROBLEM_SIZE; ++y)
        for (int x = 0; x < PROBLEM_SIZE; ++x)
            terminal_matrix[y][x] = ++i;
    terminal_matrix[LAST_POS][LAST_POS] = 0;

    State terminal_state{terminal_matrix, LAST_POS, LAST_POS};

    auto result = a_star(current_state, terminal_state);
    cout << result.value_or(-1) << '\n';

    return 0;
}
