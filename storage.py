import torch


class RolloutStorage(object):
    def __init__(self, num_steps, num_processes, obs_shape, action_shape):
        self.states = torch.zeros(num_steps + 1, num_processes, *obs_shape)
        self.rewards = torch.zeros(num_steps, num_processes, 1)
        self.value_preds = torch.zeros(num_steps + 1, num_processes, 1)
        self.action_log_probs = torch.zeros(num_steps, num_processes, 1)
        self.returns = torch.zeros(num_steps + 1, num_processes, 1)
        self.actions = torch.LongTensor(num_steps, num_processes, 1)
        self.masks = torch.zeros(num_steps, num_processes, 1)

    def cuda(self):
        self.states = self.states.cuda()
        self.rewards = self.rewards.cuda()
        self.value_preds = self.value_preds.cuda()
        self.action_log_probs = self.action_log_probs.cuda()
        self.returns = self.returns.cuda()
        self.actions = self.actions.cuda()
        self.masks = self.masks.cuda()

    def insert(self, step, current_state, action, value_pred, action_log_probs,
               reward, mask):
        self.states[step + 1].copy_(current_state)
        self.actions[step].copy_(action)
        self.value_preds[step].copy_(value_pred)
        self.action_log_probs[step].copy_(action_log_probs)
        self.rewards[step].copy_(reward)
        self.masks[step].copy_(mask)

    def compute_returns(self, next_value, use_gae, gamma, tau):
        if use_gae:
            self.value_preds[-1] = next_value
            gae = 0
            for step in reversed(range(self.rewards.size(0))):
                delta = self.rewards[step] + gamma * self.value_preds[step +
                                                                      1] * self.masks[step] - self.value_preds[step]
                gae = delta + gamma * tau * self.masks[step] * gae
                self.returns[step] = gae + self.value_preds[step]
        else:
            self.returns[-1] = next_value
            for step in reversed(range(self.rewards.size(0))):
                self.returns[step] = self.returns[step + 1] * \
                    gamma * self.masks[step] + self.rewards[step]
