import gguf
import torch


quants_mapping = {
    gguf.GGMLQuantizationType.Q2_K: gguf.Q2_K,
    gguf.GGMLQuantizationType.Q3_K: gguf.Q3_K,
    gguf.GGMLQuantizationType.Q4_0: gguf.Q4_0,
    gguf.GGMLQuantizationType.Q4_K: gguf.Q4_K,
    gguf.GGMLQuantizationType.Q4_1: gguf.Q4_1,
    gguf.GGMLQuantizationType.Q5_0: gguf.Q5_0,
    gguf.GGMLQuantizationType.Q5_1: gguf.Q5_1,
    gguf.GGMLQuantizationType.Q5_K: gguf.Q5_K,
    gguf.GGMLQuantizationType.Q6_K: gguf.Q6_K,
    gguf.GGMLQuantizationType.Q8_0: gguf.Q8_0,
}


class ParameterGGUF(torch.nn.Parameter):
    def __init__(self, tensor=None, requires_grad=False, no_init=False):
        super().__init__()
        self.is_gguf = True

        if no_init:
            return

        self.gguf_type = tensor.tensor_type
        self.gguf_real_shape = torch.Size(reversed(list(tensor.shape)))
        self.gguf_cls = quants_mapping.get(self.gguf_type, None)

    @property
    def shape(self):
        return self.gguf_real_shape

    def __new__(cls, tensor=None, requires_grad=False, no_init=False):
        return super().__new__(cls, torch.tensor(tensor.data), requires_grad=requires_grad)

    def dequantize_as_pytorch_parameter(self):
        return torch.nn.Parameter(dequantize_tensor(self), requires_grad=False)

    def to(self, *args, **kwargs):
        new = ParameterGGUF(self.data.to(*args, **kwargs), no_init=True)
        new.gguf_type = self.gguf_type
        new.gguf_real_shape = self.gguf_real_shape
        new.gguf_cls = self.gguf_cls
        return new

    def pin_memory(self, device=None):
        new = ParameterGGUF(torch.Tensor.pin_memory(self, device=device), no_init=True)
        new.gguf_type = self.gguf_type
        new.gguf_real_shape = self.gguf_real_shape
        new.gguf_cls = self.gguf_cls
        return new

    @classmethod
    def make(cls, data, gguf_type, gguf_cls, gguf_real_shape):
        new = ParameterGGUF(data, no_init=True)
        new.gguf_type = gguf_type
        new.gguf_real_shape = gguf_real_shape
        new.gguf_cls = gguf_cls
        return new


def dequantize_tensor(tensor):
    if tensor is None:
        return None

    if not hasattr(tensor, 'gguf_cls'):
        return tensor

    data = torch.tensor(tensor.data)
    gguf_cls = tensor.gguf_cls
    gguf_real_shape = tensor.gguf_real_shape

    if gguf_cls is None:
        return data

    return gguf_cls.dequantize_pytorch(data, gguf_real_shape)
