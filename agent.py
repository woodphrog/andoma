import numpy
import random
import chess
import conv
import chessenv
import os
import tensorflow.keras.optimizers as optimizers
import tensorflow
tensorflow.get_logger().setLevel('ERROR')
import movegeneration



class DeepQLearning:
    def __init__(self, env:chessenv, inputShape, memorySize, gamma, epsilon, epsilonMin, epsilonDecay):
        # Init vals
        
        self.convNet = conv.convNet(inputShape, 16, 2)
        self.model = self.convNet.model
        self.targetNet = conv.convNet(inputShape, 16, 2)
        self.targetModel = self.targetNet.model
        self.targetModel.set_weights(self.model.get_weights())
        self.memory = []
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilonMin = epsilonMin
        self.epsilonDecay = epsilonDecay
        self.env = env
        self.memorySize = memorySize
        self.batchSize = 32
        self.model.compile(optimizer=optimizers.Adam(), loss='categorical_crossentropy')
        self.model.summary()
        self.targetModel.compile(optimizer=optimizers.Adam(), loss='categorical_crossentropy')
        self.targetModel.summary()
        

    def remember(self, state, action_idx, reward, nextState, done, turn):
        self.memory.append((state, action_idx, reward, nextState, done, turn))
        if len(self.memory) > self.memorySize:
            self.memory.pop(0)

    def act(self, state):
        if numpy.random.rand() <= self.epsilon:
            #get legal moves
            legalMoves = self.env.board.legal_moves
            legalMoves = list(legalMoves)
            random_move_array, idx = env.encode_move(random.choice(legalMoves), False, self.env.board.turn)
            # print(random_move_array)
            return random_move_array, idx
        
        # filter legal moves
        legalMoves = self.env.board.legal_moves
        legalMoves = list(legalMoves)
        legalMoves = [env.encode_move(move, True, self.env.board.turn)[1] for move in legalMoves]
        actValues = self.model.predict(state, verbose=0)[0]
        actValues = [actValues[move] for move in legalMoves]
        mx = legalMoves[numpy.argmax(actValues) if self.env.board.turn else numpy.argmin(actValues)]
        arr = numpy.zeros(shape=[76, 8, 8])
        arr[mx[0]][mx[1]][mx[2]] = 1
        # print(arr)
        return arr, (mx[0], mx[1], mx[2])
    
    
    def replay(self):
        if len(self.memory) < self.batchSize:
            return
        samples = random.sample(self.memory, self.batchSize)
        for sample in samples:
            state, action, reward, nextState, done, turn = sample
            target = self.model.predict(state, verbose=0)
            if done:
                target[0][action] = reward
            else:
                # filter legal moves
                legalMoves = self.env.board.legal_moves
                legalMoves = list(legalMoves)
                legalMoves = [env.encode_move(move, True, turn)[1] for move in legalMoves]
                Q_future = self.targetModel.predict(nextState, verbose=0)[0]
                Q_future = [Q_future[move] for move in legalMoves]
                try:
                    Q_future = numpy.max(Q_future) if turn else numpy.min(Q_future)
                except:
                    Q_future = 0
                target[0][action] = reward + Q_future * self.gamma
            self.model.fit(state, target, epochs=1, verbose=0)
        if self.epsilon > self.epsilonMin:
            self.epsilon *= self.epsilonDecay

    def train(self, episodes):
        for episode in range(episodes):
            if episode % 10 == 0:
                print("Episode: ", episode)
            state = self.env.reset()
            state = numpy.reshape(state, [1, 12, 8, 8])
            done = False
            valid = True
            while (not done) and valid:
                # action, action_idx = self.act(state)
                # print(action)
                # print("!!!!!!!!!")
                # nextState, reward, done, valid = self.env.step(self.env.decode_move(action, self.env.board.turn))
                print(self.env.board)
                # reward = movegeneration.minimax(3, self.env.board, -float("inf"), float("inf"), self.env.board.turn, self)
                nextMove, reward = movegeneration.minimax_root_with_value(3, self.env.board, self)
                self.env.board.push(nextMove)
                done = self.env.board.is_game_over() or self.env.board.is_stalemate() or self.env.board.is_insufficient_material() or self.env.board.is_checkmate()
                valid = self.env.board.status() == chess.Status.VALID
                # print(self.env.board.turn)
                # print(valid)
                nextState = numpy.reshape(self.env.get_bitboard(self.env.board), [1, 12, 8, 8])
                turn = self.env.board.turn
                self.remember(state, self.env.encode_move(nextMove, True, self.env.board.turn)[1], reward if self.env.board.turn else -reward, nextState, done, turn)
                state = nextState
            self.replay()
            if episode % 10 == 0:
                print("Finished episode: ", episode)
                self.targetModel.set_weights(self.model.get_weights())
                
        self.model.save("model.h5")
        self.targetModel.save("targetModel.h5")

if __name__ == '__main__':
    env = chessenv.chessEnv(chess.Board())
    dql = DeepQLearning(env, (12, 8, 8), 500, 0.7, 0.9, 0.1, 0.95)
    dql.train(1000)
    
