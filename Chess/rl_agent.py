import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
import os
import pickle
from collections import deque
from encoder import encode_board
from utils import move_to_index
from figures import Color, Pawn, Knight, Bishop, Rook, Queen, King

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class DQN(nn.Module):
    def __init__(self, input_dim=8*8*13, output_dim=4096):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim)
        )
    def forward(self, x):
        x = x.reshape(x.size(0), -1)
        return self.net(x)

class ReplayBuffer:
    def __init__(self, capacity=200000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

    def save(self, filename='replay_buffer.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump(list(self.buffer), f)

    def load(self, filename='replay_buffer.pkl'):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.buffer = deque(pickle.load(f), maxlen=self.buffer.maxlen)

class RLAgent:
    def __init__(self, model_file='rl_model.pth', buffer_file='replay_buffer.pkl'):
        self.model_file = model_file
        self.buffer_file = buffer_file
        self.device = DEVICE

        self.q_network = DQN().to(self.device)
        self.target_network = DQN().to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.0003)

        self.memory = ReplayBuffer(capacity=200000)
        self.memory.load(buffer_file)

        self.gamma = 0.99
        self.epsilon = 0.9
        self.epsilon_min = 0.02
        self.epsilon_decay = 0.998
        self.batch_size = 64
        self.target_update = 1000
        self.steps = 0

        if os.path.exists(model_file):
            self.load_model()

    def get_all_moves(self, board, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = board.squares[r][c]
                if p and p.color == color:
                    for to in board.valid_moves(p.pos):
                        moves.append((p.pos, to))
        return moves

    def act(self, board, color):
        possible = self.get_all_moves(board, color)
        if not possible:
            return None, None
        if random.random() < self.epsilon:
            idx = random.randrange(len(possible))
            return idx, possible[idx]

        state = encode_board(board)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_vals = self.q_network(state_t).cpu().numpy()[0]

        best_idx = None
        best_val = -float('inf')
        for i, move in enumerate(possible):
            action_idx = move_to_index(move[0], move[1])
            val = q_vals[action_idx]
            if val > best_val:
                best_val = val
                best_idx = i
        return best_idx, possible[best_idx]

    def compute_reward(self, board, captured, winner, repeat=False):
        reward = -0.02  # небольшой штраф за ход
        if captured:
            value = {Pawn: 1, Knight: 3, Bishop: 3, Rook: 5, Queen: 9}.get(type(captured), 0)
            reward += value
        if repeat:
            reward -= 10
        if winner == 'black':
            reward += 100  # большая награда за победу
            print(f"*** ПОБЕДА RL! reward = {reward} ***", flush=True)  # отладка
        elif winner == 'white':
            reward -= 50
        return reward

    def remember_and_train(self, state, action, reward, next_state, done):
        self.memory.push(state, action, reward, next_state, done)
        self.steps += 1
        if self.steps % self.target_update == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        if len(self.memory) > self.batch_size:
            self._train()

    def _train(self):
        batch = self.memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = self.target_network(next_states).max(1)[0]
            target = rewards + (1 - dones) * self.gamma * next_q

        loss = nn.MSELoss()(current_q, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def save_model(self):
        torch.save(self.q_network.state_dict(), self.model_file)
        self.memory.save(self.buffer_file)

    def load_model(self):
        self.q_network.load_state_dict(torch.load(self.model_file, map_location=self.device))
        self.target_network.load_state_dict(self.q_network.state_dict())
        print("RL модель загружена")