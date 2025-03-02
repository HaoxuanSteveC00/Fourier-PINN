import numpy as np
import torch
import torch.autograd as autograd


def get_sample(N, T, s, p, q):
    # sample p nodes from Initial Condition, p nodes from Boundary Condition, q nodes from Interior

    # sample IC
    index_ic = torch.randint(s, size=(N, p))
    sample_ic_t = torch.zeros(N, p)
    sample_ic_x = index_ic/s

    # sample BC
    sample_bc = torch.rand(size=(N, p//2))
    sample_bc_t =  torch.cat([sample_bc, sample_bc],dim=1)
    sample_bc_x = torch.cat([torch.zeros(N, p//2), torch.ones(N, p//2)],dim=1)

    # sample I
    # sample_i_t = torch.rand(size=(N,q))
    # sample_i_t = torch.rand(size=(N,q))**2
    sample_i_t = -torch.cos(torch.rand(size=(N, q))*np.pi/2) + 1
    sample_i_x = torch.rand(size=(N,q))

    sample_t = torch.cat([sample_ic_t, sample_bc_t, sample_i_t], dim=1).cuda()
    sample_t.requires_grad = True
    sample_x = torch.cat([sample_ic_x, sample_bc_x, sample_i_x], dim=1).cuda()
    sample_x.requires_grad = True
    sample = torch.stack([sample_t, sample_x], dim=-1).reshape(N, (p+p+q), 2)
    return sample, sample_t, sample_x, index_ic.long()


def get_grid(N, T, s):
    gridt = torch.tensor(np.linspace(0, 1, T), dtype=torch.float).reshape(1, T, 1).repeat(N, 1, s).cuda()
    gridt.requires_grad = True
    gridx = torch.tensor(np.linspace(0, 1, s+1)[:-1], dtype=torch.float).reshape(1, 1, s).repeat(N, T, 1).cuda()
    gridx.requires_grad = True
    grid = torch.stack([gridt, gridx], dim=-1).reshape(N, T*s, 2)
    return grid, gridt, gridx


def PDELoss(model, x, t, nu):
    '''
    Compute the residual of PDE: 
        residual = u_t + u * u_x - nu * u_{xx} : (N,1)

    Params: 
        - model 
        - x, t: (x, t) pairs, (N, 2) tensor
        - nu: constant of PDE
    Return: 
        - mean of residual : scalar 
    '''
    u = model(torch.cat([x, t], dim=1))
    # First backward to compute u_x (shape: N x 1), u_t (shape: N x 1)
    grad_x, grad_t = autograd.grad(outputs=[u.sum()], inputs=[
                                   x, t], create_graph=True)
    # grad_x = grad_xt[:, 0]
    # grad_t = grad_xt[:, 1]

    # Second backward to compute u_{xx} (shape N x 1)

    gradgrad_x, = autograd.grad(
        outputs=[grad_x.sum()], inputs=[x], create_graph=True)
    # gradgrad_x = gradgrad[:, 0]

    residual = grad_t + u * grad_x - nu * gradgrad_x
    return residual


def requires_grad(model, flag=True):
    for p in model.parameters():
        p.requires_grad = flag


def zero_grad(params):
    '''
    set grad field to 0
    '''
    if isinstance(params, torch.Tensor):
        if params.grad is not None:
            params.grad.detach()
            params.grad.zero_()
    else:
        for p in params:
            if p.grad is not None:
                p.grad.detach()
                p.grad.zero_()


def count_params(net):
    count = 0
    for p in net.parameters():
        count += p.numel()
    return count

