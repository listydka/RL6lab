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

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class DQN(nn.Module):
    def __init__(self, input_dim=832, output_dim=4096):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, output_dim)
        )
    def forward(self, x):
        x = x.reshape(x.size(0), -1)
        return self.net(x)

class ReplayBuffer:
    def __init__(self, capacity=100000):
        self.buffer = deque(maxlen=capacity)
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)
    def __len__(self):
        return len(self.buffer)
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(list(self.buffer), f)
    def load(self, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.buffer = deque(pickle.load(f), maxlen=self.buffer.maxlen)

class RLAgent:
    def __init__(self, model_file='rl_simple.pth', buffer_file='replay_simple.pkl'):
        self.model_file = model_file
        self.buffer_file = buffer_file
        self.device = DEVICE
        self.q_network = DQN().to(self.device)
        self.target_network = DQN().to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        self.memory = ReplayBuffer(capacity=100000)
        self.memory.load(buffer_file)
        self.gamma = 0.99
        self.epsilon = 0.9
        self.epsilon_min = 0.02
        self.epsilon_decay = 0.999   # медленное падение (после каждой игры)
        self.batch_size = 64
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
        moves = self.get_all_moves(board, color)
        if not moves:
            return None, None
        if random.random() < self.epsilon:
            idx = random.randrange(len(moves))
            return idx, moves[idx]
        state = encode_board(board).flatten()
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q = self.q_network(state_t).cpu().numpy()[0]
        best_idx = None
        best_val = -1e9
        for i, move in enumerate(moves):
            a_idx = move_to_index(move[0], move[1])
            val = q[a_idx]
            if val > best_val:
                best_val = val
                best_idx = i
        return best_idx, moves[best_idx]

    def remember_and_train(self, state, action, reward, next_state, done):
        self.memory.push(state, action, reward, next_state, done)
        if len(self.memory) > self.batch_size:
            self._train()
        self.steps += 1
        if self.steps % 1000 == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

    def _train(self):
        batch = self.memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        current = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = self.target_network(next_states).max(1)[0]
            target = rewards + (1 - dones) * self.gamma * next_q
        loss = nn.MSELoss()(current, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        # НЕ ОБНОВЛЯЕМ epsilon здесь!

    def save_model(self):
        torch.save(self.q_network.state_dict(), self.model_file)
        self.memory.save(self.buffer_file)

    def load_model(self):
        self.q_network.load_state_dict(torch.load(self.model_file, map_location=self.device))
        self.target_network.load_state_dict(self.q_network.state_dict())