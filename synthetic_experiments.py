import numpy as np
nax = np.newaxis
import os

import config
import experiments
import observations

NUM_ROWS = 200
NUM_COLS = 200
NUM_COMPONENTS = 10

def generate_ar(nrows, ncols, a):
    X = np.zeros((nrows, ncols))
    X[0,:] = np.random.normal(size=ncols)
    for i in range(1, nrows):
        X[i,:] = a * X[i-1,:] + np.random.normal(0., np.sqrt(1-a**2), size=ncols)
    return X

def generate_data(data_str, nrows, ncols, ncomp, return_components=False):
    IBP_ALPHA = 2.
    pi_crp = np.ones(ncomp) / ncomp
    pi_ibp = np.ones(ncomp) * IBP_ALPHA / ncomp

    if data_str[-1] == 'T':
        data_str = data_str[:-1]
        transpose = True
        nrows, ncols = ncols, nrows
    else:
        transpose = False
    
    if data_str == 'pmf':
        U = np.random.normal(0., 1., size=(nrows, ncomp))
        V = np.random.normal(0., 1., size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)
        
    elif data_str == 'mog':
        U = np.random.multinomial(1, pi_crp, size=nrows)
        V = np.random.normal(0., 1., size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)

    elif data_str == 'ibp':
        U = np.random.binomial(1, pi_ibp[nax,:], size=(nrows, ncomp))
        V = np.random.normal(0., 1., size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)

    elif data_str == 'sparse':
        Z = np.random.normal(0., 1., size=(nrows, ncomp))
        U = np.random.normal(0., np.exp(Z))
        V = np.random.normal(0., 1., size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)
        

    elif data_str == 'gsm':
        U_inner = np.random.normal(0., 1., size=(nrows, 1))
        V_inner = np.random.normal(0., 1., size=(1, ncomp))
        Z = np.random.normal(U_inner * V_inner, 1.)
        #Z = 2. * Z / np.sqrt(np.mean(Z**2))

        U = np.random.normal(0., np.exp(Z))
        V = np.random.normal(0., 1., size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)

    elif data_str == 'irm':
        U = np.random.multinomial(1, pi_crp, size=nrows)
        R = np.random.normal(0., 1., size=(ncomp, ncomp))
        V = np.random.multinomial(1, pi_crp, size=ncols).T
        data = np.dot(np.dot(U, R), V)
        components = (U, R, V)

    elif data_str == 'bmf':
        U = np.random.binomial(1, pi_ibp[nax,:], size=(nrows, ncomp))
        R = np.random.normal(0., 1., size=(ncomp, ncomp))
        V = np.random.binomial(1, pi_ibp[nax,:], size=(ncols, ncomp)).T
        data = np.dot(np.dot(U, R), V)
        components = (U, R, V)

    elif data_str == 'mgb':
        U = np.random.multinomial(1, pi_crp, size=nrows)
        R = np.random.normal(0., 1., size=(ncomp, ncomp))
        V = np.random.binomial(1, pi_ibp[nax,:], size=(ncols, ncomp)).T
        data = np.dot(np.dot(U, R), V)
        components = (U, R, V)

    elif data_str == 'chain':
        data = generate_ar(nrows, ncols, 0.9)
        components = (data)

    elif data_str == 'kf':
        U = generate_ar(nrows, ncomp, 0.9)
        V = np.random.normal(size=(ncomp, ncols))
        data = np.dot(U, V)
        components = (U, V)

    elif data_str == 'bctf':
        temp1, (U1, V1) = generate_data('mog', nrows, ncols, ncomp, True)
        F1 = np.random.normal(temp1, 1.)
        temp2, (U2, V2) = generate_data('mog', nrows, ncols, ncomp, True)
        F2 = np.random.normal(temp2, 1.)
        data = np.dot(F1, F2.T)
        components = (U1, V1, F1, U2, V2, F2)
        

    data /= np.std(data)

    if transpose:
        data = data.T

    if return_components:
        return data, components
    else:
        return data


ALL_MODELS = ['pmf', 'mog', 'ibp', 'chain', 'irm', 'bmf', 'kf', 'bctf', 'sparse', 'gsm']


def init_experiment():
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            name = 'synthetic/%s/%s' % (condition, model)
            print condition, model
            data, components = generate_data(model, NUM_ROWS, NUM_COLS, NUM_COMPONENTS, True)
            clean_data_matrix = observations.DataMatrix.from_real_values(data)
            noise_var = float(condition)
            noisy_data = np.random.normal(data, np.sqrt(noise_var))
            data_matrix = observations.DataMatrix.from_real_values(noisy_data)
            experiments.init_experiment(name, data_matrix, components, clean_data_matrix=clean_data_matrix)
        
def init_level(level, override=False):
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            print condition, model
            experiments.init_level('synthetic/%s/%s' % (condition, model), level, override=override)

def collect_scores_for_level(level):
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            print condition, model
            experiments.collect_scores_for_level('synthetic/%s/%s' % (condition, model), level)



def write_jobs_init(level):
    if level == 1:
        raise RuntimeError('No need for initialization for level 1.')
    jobs = []
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            name = 'synthetic/%s/%s' % (condition, model)
            winning_models = experiments.list_winning_models(name, level - 1)
            if winning_models[-1] == '---':
                continue
            jobs += experiments.list_init_jobs(name, level)
    experiments.write_jobs(jobs, os.path.join(config.JOBS_PATH, 'synthetic/jobs.txt'))

def write_jobs_for_level(level):
    jobs = []
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            name = 'synthetic/%s/%s' % (condition, model)
            if level > 1:
                winning_models = experiments.list_winning_models(name, level - 1)
                if winning_models[-1] == '---':
                    continue
            jobs += experiments.list_jobs(name, level)
    experiments.write_jobs(jobs, os.path.join(config.JOBS_PATH, 'synthetic/jobs.txt'))

def write_jobs_failed(level):
    jobs = []
    for condition in ['0.1', '1.0', '3.0', '10.0']:
        for model in ALL_MODELS:
            jobs += experiments.list_jobs_failed('synthetic/%s/%s' % (condition, model), level)
    experiments.write_jobs(jobs, os.path.join(config.JOBS_PATH, 'synthetic/jobs.txt'))