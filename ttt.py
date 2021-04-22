class TicTacToe:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.turn = p1
        self.gameOver = False
        self.board = [":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"]
        self.count = 0
        self.line = ""

    def change_turn(self):
        if self.turn == self.p1:
            self.turn = self.p2
        else:
            self.turn = self.p1
