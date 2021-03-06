import sys
import random
import heapq

class Piece:

    movement = {"King": [(1, 1, 1), (1, 0, 1), (1, -1, 1), (0, -1, 1), (-1, -1, 1), (-1, 0, 1), (-1, 1, 1), (0, 1, 1)],
                "Rook": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0)],
                "Bishop": [(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Queen": [(1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 1, 0), (1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)],
                "Knight": [],
                "Obstacle": [],
                "Empty": [],
                }

    def __init__(self, pieceType: str) -> None:
        self.type = pieceType

    def isEmpty(self) -> bool:
        return self.type == "Empty"

    def possibleMovement(self):
        return self.movement[self.type]


class Board:


    def __init__(self, x: int, y: int) -> None:
        self.enemyPos = {}  # (x, y) -> Enemy type
        self.obstaclePos = []
        self.board_size_x = x
        self.board_size_y = y

        self.blocked = []
        for i in range(x):
            self.blocked.append([False, ] * y)

    def addEnemyPiece(self, pieceType: str, x: int, y: int) -> None:
        self.enemyPos[(x, y)] = Piece(pieceType)
        self.blocked[x][y] = True

    def removeEnemyPiece(self, x: int, y: int) -> None:
        self.enemyPos.pop((x, y))
        self.blocked[x][y] = False

    def addObstaclePiece(self, x: int, y: int) -> None:
        self.obstaclePos.append((x, y))
        self.blocked[x][y] = True

    def isWithinBoard(self, x, y) -> bool:
        if (0 > x or x >= self.board_size_x) or (0 > y or y >= self.board_size_y):
            return False
        return True

    def isThreatened(self, x, y) -> bool:
        # Must update threatened first!!!
        return self.numOfEnemiesThreatening[x][y] > 0

    def isBlocked(self, x, y) -> bool:
        return (x, y) in self.obstaclePos or (x, y) in self.enemyPos.keys()

    def setThreatened(self, x, y) -> None:
        if (x, y) in self.enemyPos:
            self.numOfEnemiesThreatening[x][y] += 1

    def updateThreatened(self):

        # Reset number of pieces threatening a piece
        self.numOfEnemiesThreatening = []
        for i in range(self.board_size_x):
            self.numOfEnemiesThreatening.append([0, ] * self.board_size_y)

        for x, y in self.enemyPos:
            piece: Piece = self.enemyPos[(x, y)]
            if piece.type == "Knight":
                for twoSteps in [-2, 2]:
                    for oneStep in [-1, 1]:
                        if self.isWithinBoard(x + twoSteps, y+oneStep):
                            self.setThreatened(x+twoSteps, y+oneStep)
                        if self.isWithinBoard(x + oneStep, y+twoSteps):
                            self.setThreatened(x+oneStep, y+twoSteps)
            else:
                transModel = pieceMovementModel(
                    self, x, y, piece.possibleMovement())
                for possibleX, possibleY in transModel.getAllPossibleNewPos():
                    self.setThreatened(possibleX, possibleY)
        
        # calculate to find out the ranking of threatened
        self.numOfEnemiesThreatening_ranked = []
        for x, y in self.enemyPos:
            if self.numOfEnemiesThreatening[x][y] == 0:
                continue
            heapq.heappush(self.numOfEnemiesThreatening_ranked, (x, y))
    
    def getTopThreatened(self, n: int):
        return heapq.nlargest(n, self.numOfEnemiesThreatening_ranked)

    def getMostThreatenedPos(self):
        highestThreatened = 0
        resultX, resultY = list(self.enemyPos.keys())[0]

        for x, y in self.enemyPos:
            # print(x, y, self.numOfEnemiesThreatening[x][y])
            if self.numOfEnemiesThreatening[x][y] > highestThreatened:
                highestThreatened = self.numOfEnemiesThreatening[x][y]
                resultX, resultY = x, y

        return (resultX, resultY, highestThreatened)

    def setGoal(self, K: int) -> None:
        self.K = K

    def goalCheck(self) -> bool:
        return len(self.enemyPos) >= self.K and self.sumOfThreatened() == 0
    
    def sumOfThreatened(self):
        sum = 0
        for x, y in self.enemyPos:
            sum += self.numOfEnemiesThreatening[x][y]
        return sum


class pieceMovementModel():

    def __init__(self, board: Board, x: int, y: int, piece_movements):
        self.x = x
        self.y = y
        self.board = board
        self.movements = piece_movements

    def moveToDirection(self, x_change: int, y_change: int):
        new_x = self.x + x_change
        new_y = self.y + y_change
        return (new_x, new_y)

    def getAllPossibleMovementToDirection(self, x_change: int, y_change: int, max_steps=0):
        '''Get all the positions that the piece can move to, including position that are being threatened by other pieces'''
        if max_steps == 0:
            max_steps = max(self.board.board_size_x, self.board.board_size_y)
        steps = []
        for i in range(max_steps):
            new_pos = self.moveToDirection((i+1) * x_change, (i+1) * y_change)
            if not self.board.isWithinBoard(new_pos[0], new_pos[1]):
                break
            if self.board.isBlocked(new_pos[0], new_pos[1]):
                steps.append(new_pos)
                break
            steps.append(new_pos)
        return steps

    def getAllPossibleNewPos(self):
        steps = []
        for movement in self.movements:
            xChange, yChange, maxSteps = movement
            steps.extend(self.getAllPossibleMovementToDirection(
                xChange, yChange, maxSteps))
        return steps

    def getAllAllowedMovementToDirection(self, x_change: int, y_change: int, max_steps=0):
        '''Get all the positions that the piece can move to without being threatened'''
        if max_steps == 0:
            max_steps = max(self.board.board_size_x, self.board.board_size_y)
        steps = []
        for i in range(max_steps):
            new_pos = self.moveToDirection((i+1) * x_change, (i+1) * y_change)
            if not self.board.isWithinBoard(new_pos[0], new_pos[1]) or self.board.isBlocked(new_pos[0], new_pos[1]):
                break
            if self.board.isThreatened(new_pos[0], new_pos[1]):
                continue
            steps.append(new_pos)
        return steps

    def getAllAllowedNewPos(self):
        steps = []
        for movement in self.movements:
            xChange, yChange, maxSteps = movement
            steps.extend(self.getAllAllowedMovementToDirection(
                xChange, yChange, maxSteps))
        return steps


class State:

    def __init__(self) -> None:
        self.board = []

    def initBoard(self, x: int, y: int) -> Board:
        self.board = Board(x, y)

    def setBoard(self, board: Board) -> None:
        self.board = board


def letterToX(character) -> int:
    return ord(character) - ord('a')


def PosToXY(pos) -> tuple:
    return (letterToX(pos[0]), int(pos[1:]))


def XYtoPos(xy: tuple) -> tuple:
    xCharVal: int = xy[0]+ord('a')
    return (chr(xCharVal), xy[1])