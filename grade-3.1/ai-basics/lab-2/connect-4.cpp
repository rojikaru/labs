#include <bits/stdc++.h>
using namespace std;

constexpr int PROBLEM_SIZE = 4;

char get_opponent(char player)
{
    return (player == 'X') ? 'O' : 'X';
}

int directions[4][2] = {{1, 0}, {0, 1}, {1, 1}, {1, -1}};
bool has_won(const vector<vector<char>> &board, char player)
{
    for (int r = 0; r < PROBLEM_SIZE; r++)
        for (int c = 0; c < PROBLEM_SIZE; c++)
            for (int d = 0; d < 4; d++)
            {
                int cnt = 0;
                for (int i = 0; i < PROBLEM_SIZE; i++)
                {
                    int nr = r + i * directions[d][0];
                    int nc = c + i * directions[d][1];
                    if (nr >= 0 && nr < PROBLEM_SIZE &&
                        nc >= 0 && nc < PROBLEM_SIZE &&
                        board[nr][nc] == player)
                        cnt++;
                    else
                        break;
                }
                if (cnt == PROBLEM_SIZE)
                    return true;
            }

    return false;
}

bool is_draw(const vector<vector<char>> &board)
{
    for (int c = 0; c < PROBLEM_SIZE; ++c)
        if (board[0][c] == '.')
            return false;
    return true;
}

bool can_make_turn(const vector<vector<char>> &board, int col)
{
    return col >= 0 && col < PROBLEM_SIZE && board[0][col] == '.';
}

constexpr int w[PROBLEM_SIZE][PROBLEM_SIZE] = {
    {3, 2, 2, 3},
    {2, 3, 3, 2},
    {2, 3, 3, 2},
    {3, 2, 2, 3}};

int turn_score(char playerChar, const vector<vector<char>> &board, int depth)
{
    if (has_won(board, playerChar))
        return 1000 + depth; // Prefer faster wins
    if (has_won(board, get_opponent(playerChar)))
        return -1000 - depth; // Prefer slower losses
    if (is_draw(board))
        return 0;

    // Simple positional evaluation
    int score = 0;
    for (int i = 0; i < PROBLEM_SIZE; ++i)
        for (int j = 0; j < PROBLEM_SIZE; ++j)
            if (board[i][j] == playerChar)
                score += w[i][j];
            else if (board[i][j] == get_opponent(playerChar))
                score -= w[i][j];
    return score;
}

int make_turn(vector<vector<char>> &board, int move, char player)
{
    for (int row = PROBLEM_SIZE - 1; row >= 0; --row)
        if (board[row][move] == '.')
        {
            board[row][move] = player;
            return row; // return the row we placed in
        }
    return -1; // shouldn't happen
}

void undo_turn(vector<vector<char>> &board, int col)
{
    for (int row = 0; row < PROBLEM_SIZE; ++row)
        if (board[row][col] != '.')
        {
            board[row][col] = '.';
            return;
        }
}

// pair<score, move>
pair<int, int> minimax_best_move(
    char player, vector<vector<char>> &board, int depth,
    bool is_maximizing, int alpha = INT_MIN, int beta = INT_MAX)
{
    // Check for terminal states
    if (has_won(board, player))
        return {1000 + depth, -1};
    if (has_won(board, get_opponent(player)))
        return {-1000 - depth, -1};
    if (is_draw(board))
        return {0, -1};
    if (depth == 0)
        return {turn_score(player, board, depth), -1};

    char current = is_maximizing ? player : get_opponent(player);
    int top_score = is_maximizing ? INT_MIN : INT_MAX;
    int top_move = -1;

    // Center columns first for better pruning
    int moveOrder[PROBLEM_SIZE] = {1, 2, 0, 3};

    for (int i = 0; i < PROBLEM_SIZE; ++i)
    {
        int move = moveOrder[i];
        if (!can_make_turn(board, move))
            continue;

        make_turn(board, move, current);
        auto [score, _] = minimax_best_move(
            player, board, depth - 1,
            !is_maximizing, alpha, beta);
        undo_turn(board, move);

        if (beta <= alpha)
            break;

        if (is_maximizing && score > top_score)
        {
            top_score = score;
            top_move = move;
            alpha = max(alpha, score);
        }
        else if (!is_maximizing && score < top_score)
        {
            top_score = score;
            top_move = move;
            beta = min(beta, score);
        }
    }

    return {top_score, top_move};
}

int make_human_turn(char human_player, vector<vector<char>> &board)
{
    // Check for immediate win first
    for (int move = 0; move < PROBLEM_SIZE; ++move)
    {
        if (!can_make_turn(board, move))
            continue;
        make_turn(board, move, human_player);
        if (has_won(board, human_player))
        {
            undo_turn(board, move);
            return move;
        }
        undo_turn(board, move);
    }

    // Check for immediate loss prevention
    for (int move = 0; move < PROBLEM_SIZE; ++move)
    {
        if (!can_make_turn(board, move))
            continue;
        make_turn(board, move, get_opponent(human_player));
        if (has_won(board, get_opponent(human_player)))
        {
            undo_turn(board, move);
            return move;
        }
        undo_turn(board, move);
    }

    // Default to minimax decision
    return minimax_best_move(human_player, board, 14, true).second;
}

int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    char human_player, current_player;
    if (!(cin >> human_player >> current_player))
        return 0;
    char opponent = get_opponent(human_player);

    vector<vector<char>> board(PROBLEM_SIZE, vector<char>(PROBLEM_SIZE, '.'));
    string line;
    for (int i = 0; i < PROBLEM_SIZE; ++i)
    {
        cin >> line;
        for (int j = 0; j < PROBLEM_SIZE; ++j)
            board[i][j] = line[j];
    }

    while (true)
    {
        // Check if game is already over
        if (has_won(board, human_player) || has_won(board, opponent) || is_draw(board))
            break;

        if (current_player != human_player)
        {
            int move;
            cin >> move;
            if (move == 0)
                break;
            move--; // Convert to 0-based index

            make_turn(board, move, opponent);
            current_player = human_player;

            continue;
        }

        int move = make_human_turn(human_player, board);
        if (move < 0 || move >= PROBLEM_SIZE || !can_make_turn(board, move))
        {
            move = -1;
            for (int c = 0; c < PROBLEM_SIZE; ++c)
            {
                if (can_make_turn(board, c))
                {
                    move = c;
                    break;
                }
            }
            if (move == -1)
                return 0;
        }

        cout << move + 1 << '\n';
        cout.flush();

        make_turn(board, move, human_player);
        current_player = get_opponent(human_player);
    }

    return 0;
}
