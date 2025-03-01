"""Implementation for WD My Cloud EX2 Ultra."""

from typing import List

from ..models.disk import DiskInfo, SmartAttribute, SmartInfo
from ..models.system import SystemInfo, RaidInfo, VolumeInfo, LogEntry
from .base import WDNasDevice
from datetime import datetime


class EX2UltraDevice(WDNasDevice):
    """Implementation for WD My Cloud EX2 Ultra."""

    def get_all_data(self) -> None:
        """Get all data from the device."""
        self.all_data = self.client.get_all_data()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

    def get_system_info(self) -> SystemInfo:
        """Get system information.

        Returns:
            SystemInfo: System information for the device

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raids = [
            RaidInfo(
                id=int(raid["id"]),
                level=raid["level"],
                chunk_size=int(raid["chunk_size"]),
                num_of_total_disks=int(raid["num_of_total_disks"]),
                num_of_raid_disks=int(raid["num_of_raid_disks"]),
                num_of_active_disks=int(raid["num_of_active_disks"]),
                num_of_working_disks=int(raid["num_of_working_disks"]),
                num_of_spare_disks=int(raid["num_of_spare_disks"]),
                num_of_failed_disks=int(raid["num_of_failed_disks"]),
                raid_disks=raid["raid_disks"],
                spare_disks=raid["spare_disks"],
                failed_disks=raid["failed_disks"],
                rebuilding_disks=raid["rebuilding_disks"],
                size=int(raid["size"]),
                used_size=int(raid["used_size"]),
                min_req_size=int(raid["min_req_size"]),
                state=raid["state"],
                state_detail=raid["state_detail"],
                uuid=raid["uuid"],
                dev=raid["dev"],
                ar=int(raid["ar"]),
                expand_size=int(raid["expand_size"]),
                expand_no_replace=int(raid["expand_no_replace"]),
                migrate_from=raid["migrate_from"],
                migrate_to=raid["migrate_to"],
                recover_failed=int(raid["recover_failed"]),
                reshape_failed=int(raid["reshape_failed"]),
                dirty=int(raid["dirty"]),
            )
            for raid in self.all_data["system_status"]["config"]["raids"]["raid"]
        ]

        volumes = [
            VolumeInfo(
                id=int(volume["num"]),
                name=volume["name"],
                label=volume["label"],
                mount_point=volume["mount_point"],
                encrypted=volume["encrypted"] == "true",
                device_path=volume["device_path"],
                unlocked=volume["unlocked"] == "true",
                mounted=volume["mounted"] == "true",
                size=int(volume["size"]),
                uuid=volume["uuid"],
                roaming=volume["roaming"] == "true",
                used_size=int(volume["used_size"]),
                raid_level=volume["raid_level"],
                raid_state=volume["raid_state"],
                raid_state_detail=volume["raid_state_detail"],
                state=volume["state"],
            )
            for volume in self.all_data["system_status"]["config"]["vols"]["vol"]
        ]

        logs = [
            LogEntry(
                timestamp=log["cell"][1],
                level=log["cell"][0],
                service=log["cell"][2],
                message=log["cell"][3],
            )
            for log in self.all_data["system_logs"]["rows"]
        ]

        return SystemInfo(
            serial_number=self.all_data["device_info"]["serial_number"],
            name=self.all_data["device_info"]["name"],
            workgroup=self.all_data["device_info"]["workgroup"],
            description=self.all_data["device_info"]["description"],
            firmware_version=self.all_data["firmware_version"]["fw"],
            oled=self.all_data["firmware_version"]["oled"],
            fan_speed=int(self.all_data["home_info"]["fan"]),
            lan_r_speed=int(self.all_data["system_status"]["lan_r_speed"]),
            lan_t_speed=int(self.all_data["system_status"]["lan_t_speed"]),
            lan2_r_speed=int(self.all_data["system_status"]["lan2_r_speed"]),
            lan2_t_speed=int(self.all_data["system_status"]["lan2_t_speed"]),
            memory_total=int(self.all_data["system_status"]["mem_total"]),
            memory_free=int(self.all_data["system_status"]["mem_free"]),
            memory_buffers=int(self.all_data["system_status"]["buffers"]),
            memory_cached=int(self.all_data["system_status"]["cached"]),
            cpu_usage=float(int(self.all_data["system_status"]["cpu"].replace("%", "")) / 100.0),
            raids=raids,
            volumes=volumes,
            logs=logs,
        )

    def get_disks(self) -> List[DiskInfo]:
        """Get information about all disks.

        Returns:
            List[DiskInfo]: List of disk information objects
        """

        disks: List[DiskInfo] = []

        for disk_name, disk_smart_data in self.all_data["disks_smart_info"].items():

            disk_from_system = self.all_data["system_info"]["config"]["disks"]["disk"]
            disk_from_system = next(
                (disk for disk in disk_from_system if disk["name"] == disk_name), None
            )
            if not disk_from_system:
                raise ValueError(f"Disk {disk_name} not found in system info")

            smart_attributes = [
                SmartAttribute(
                    id=int(attr["id"]),
                    name=attr["name"],
                    value=int(attr["value"]),
                    worst=int(attr["worst"]),
                    threshold=int(attr["threshold"]),
                )
                for attr in disk_smart_data["attributes"]
            ]

            # Example: <result>Pass [2025/02/28 02:07:22]</result>
            result = disk_from_system["smart"]["result"].split(" ")[0]
            date_str = (
                disk_from_system["smart"]["result"].split("[")[1].split("]")[0].strip()
            )

            smart_info = SmartInfo(
                result=result,
                test_type=disk_from_system["smart"]["test_type"],
                date=datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S"),
                percent=float(int(disk_smart_data["percent"]) / 100),
                attributes=smart_attributes,
            )

            disks.append(
                DiskInfo(
                    name=disk_name,
                    scsi_path=disk_from_system["scsi_path"],
                    connected=disk_from_system["connected"] == "1",
                    vendor=disk_from_system["vendor"],
                    model=disk_from_system["model"],
                    revision=disk_from_system["revision"],
                    serial=disk_from_system["serial"],
                    device_path=disk_from_system["device_path"],
                    size_bytes=int(disk_from_system["size"]),
                    partition_count=int(disk_from_system["partition_count"]),
                    allowed=disk_from_system["allowed"] == "1",
                    raid_uuid=disk_from_system["raid_uuid"],
                    failed=disk_from_system["failed"] == "1",
                    healthy=disk_from_system["healthy"] == "1",
                    removable=disk_from_system["removable"] == "1",
                    roaming=disk_from_system["roaming"],
                    smart_info=smart_info,
                    temperature=int(disk_from_system["temperature"]),
                    over_temp=disk_from_system["over_temp"] == "1",
                    sleep=disk_from_system["sleep"] == "1",
                )
            )
        return disks
