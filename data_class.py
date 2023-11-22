from dataclasses import dataclass

@dataclass
class NetworkInfo:
    nic_type : str = None
    pf_list : [] = None
    pf_pci_list : [] = None
    vf_list : [] = None
    vf_pci_list : [] = None

    def __init__(self, nic_type : str, pf_list : [], pf_pci_list: [], **kwargs):
        self.nic_type = nic_type
        self.pf_list=pf_list
        self.pf_pci_list=pf_pci_list
