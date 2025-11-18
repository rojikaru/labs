#include <iostream>
#include <vector>
#include <climits>
#include <algorithm>
#include <unordered_map>

using namespace std;

constexpr int PROBLEM_SIZE = 5, CONNECT_N = 4;
unordered_map<uint64_t, int64_t> memo;

char get_opponent(char player)
{
  return (player == 'X') ? 'O' : 'X';
}

uint64_t hash_board(const vector<string> &board)
{
  uint64_t key = 0;

  for (int row = 0; row < PROBLEM_SIZE; ++row)
    for (int col = 0; col < PROBLEM_SIZE; ++col)
    {
      key *= 3ULL;
      char cell = board[row][col];
      if (cell == 'X')
        key += 1ULL;
      else if (cell == 'O')
        key += 2ULL;
    }

  return key;
}

pair<int, int> make_move(vector<string>& board, int col, char player)
{
  for (int row = PROBLEM_SIZE - 1; row >= 0; row--)
    if (board[row][col] == '.')
    {
      board[row][col] = player;
      return {row, col};
    }
    
  return {-1, -1};
}

void undo_move(vector<string>& board, int row, int col)
{
  board[row][col] = '.';
}

bool has_won(const vector<string>& board, char player)
{
  // Horizontal for each row
  for (int row = 0; row < PROBLEM_SIZE; row++)
    for (int col = 0; col <= 1; col++)
      for (int k = 0; k < CONNECT_N; k++)
      {
        if (board[row][col + k] != player)
          break;
        if (k == CONNECT_N - 1)
          return true;
      }

  // Vertical for each column
  for (int col = 0; col < PROBLEM_SIZE; col++)
    for (int row = 0; row <= 1; row++)
      for (int k = 0; k < CONNECT_N; k++)
      {
        if (board[row + k][col] != player)
          break;
        if (k == CONNECT_N - 1)
          return true;
      }

  // Diagonal (Top-left to Bottom-right)
  for (int row = 0; row <= 1; row++)
    for (int col = 0; col <= 1; col++)
      for (int k = 0; k < CONNECT_N; k++)
      {
        if (board[row + k][col + k] != player)
          break;
        if (k == CONNECT_N - 1)
          return true;
      }

  // Diagonal (Top-right to Bottom-left)
  for (int row = 0; row <= 1; row++)
    for (int col = 3; col < PROBLEM_SIZE; col++)
      for (int k = 0; k < CONNECT_N; k++)
      {
        if (board[row + k][col - k] != player)
          break;
        if (k == CONNECT_N - 1)
          return true;
      }

  return false;
}

bool can_make_move(const vector<string>& board, int col)
{
  return board[0][col] == '.';
}

int64_t minimax(
  vector<string>& board, 
  char maximizing_player, char current, 
  bool is_maximizing, 
  int64_t alpha = INT64_MIN, int64_t beta = INT64_MAX)
{
  uint64_t hash = (hash_board(board) << 3) | ((is_maximizing) << 1) | (maximizing_player == 'X');
  if (memo.count(hash))
    return memo[hash];

  if (has_won(board, maximizing_player))
    return 1;
  if (has_won(board, get_opponent(maximizing_player)))
    return -1;

  const auto order = {2, 1, 3, 0, 4};
  int64_t top_score = is_maximizing ? -2 : 2;
  bool cut = false;

  for (int col : order)
  {
    if (!can_make_move(board, col))
      continue;

    auto [turn_row, turn_col] = make_move(board, col, current);
    int64_t score = minimax(board, maximizing_player, get_opponent(current), !is_maximizing, alpha, beta);
    undo_move(board, turn_row, turn_col);
    
    if (is_maximizing)
    {
      top_score = max(top_score, score);
      alpha = max(alpha, top_score);
    }
    else
    {
      top_score = min(top_score, score);
      beta = min(beta, top_score);
    }

    if (beta <= alpha)
    {
      cut = true;
      break;
    }

    if (top_score == 1 && is_maximizing)
      break;
  }

  // Draw case adjustment
  if (top_score == -2 || top_score == 2)
    top_score = 0;

  if (!cut || top_score == 1)
    memo.emplace(hash, top_score);

  return top_score;
}

char next_player(const vector<string> &board)
{
  int x = 0, o = 0;
  for (auto &row : board)
    for (char c : row)
    {
      if (c == 'X')
        x++;
      else if (c == 'O')
        o++;
    }
  return (x <= o ? 'X' : 'O');
}

int main()
{
  ios_base::sync_with_stdio(false);
  cin.tie(nullptr);

  int num_tests;
  cin >> num_tests;

  vector<string> board(5);
  while (num_tests--)
  {
    for (int i = 0; i < 5; i++)
      cin >> board[i];

    char turn = next_player(board);
    int64_t result = minimax(board, turn, turn, true);

    if (result > 0)
      cout << "WIN\n";
    else if (result < 0)
      cout << "LOSE\n";
    else
      cout << "DRAW\n";
  }
  return 0;
}
