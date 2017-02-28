#!/usr/bin/python
import log
import copy


def add_relative_time(data):
    t0 = max([e.get('time') for e in data])
    for e in data:
        e['relative_time_sec'] = float((t0 - e['time']).total_seconds())
    return data


def add_virtual_time(samples, threshold_sec):
    prev = None
    virtual_time = 0
    for curr in samples:
        if prev is not None:
            t1 = prev['relative_time_sec']
            t2 = curr['relative_time_sec']
            delta = t2 - t1
            is_overtime = delta >= threshold_sec
            is_status_changed = curr['status'] != prev['status']
            if not is_overtime and not is_status_changed:
                virtual_time += delta
        curr['virtual_time_hour'] = virtual_time/(60*60)
        prev = copy.deepcopy(curr)
    return samples


def separate_by_status(samples):
    result = []
    chunk = []
    prev = None
    for curr in samples:
        if prev is not None:
            if curr['status'] != prev['status']:
                result.append(chunk)
                chunk = []
        chunk.append(curr)
        prev = curr
    result.append(chunk)
    return result


def extract_plot_data(batch):
    status = None if len(batch) == 0 else batch[0].get('status')
    xs = filter(
        lambda x: x is not None, [e.get('virtual_time_hour') for e in batch])
    ys = filter(
        lambda x: x is not None, [e.get('capacity') for e in batch])
    return {
        'status': status,
        'xs': xs,
        'ys': ys
    }


class History:

    def __init__(self, log_data=[], threshold_sec=15*60):
        data = add_relative_time(log_data)
        data = sorted(data, key=lambda e: e['relative_time_sec'])
        data = add_virtual_time(data, threshold_sec)
        self._data = data
        self._plot_data = []
        self._plot_xoffset = 0
        self._plot_xlimit = 12.0

    def data(self):
        return self._data

    def set_plot_data_xoffset(self, xoffset):
        self._plot_xoffset = xoffset

    def set_plot_data_xlimit(self, hours):
        self._plot_xlimit = hours

    def get_recent_history(self, limit):
        data = filter(lambda d: d['virtual_time_hour'] < limit, self._data)
        return data

    def calculate_plot_data(self):
        limit = self._plot_xlimit - self._plot_xoffset
        data = self.get_recent_history(limit)
        # shift
        for e in data:
            e['virtual_time_hour'] += self._plot_xoffset
        data = separate_by_status(data)
        # exptract plot data
        self._plot_data = [extract_plot_data(batch) for batch in data]

    def plot_data(self, status):
        return [x for x in self._plot_data if x.get('status') == status]