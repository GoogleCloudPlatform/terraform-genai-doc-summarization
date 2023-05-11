# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

@dataclass
class CloudEventDataMock:
    bucket:  str
    name:  str
    metageneration:  str
    timeCreated:  str
    updated:  str

    def __getitem__(self, key):
        return self.__getattribute__(key)


@dataclass
class CloudEventMock:
    data:  str
    id:  str
    type:  str

    def __getitem__(self, key):
      if key == 'id':
        return self.id
      elif key == 'type':
        return self.type
      else:
        raise RuntimeError(f'Unknown key: {key}')

MOCK_CLOUD_EVENT = CloudEventMock(
    id='7631145714375969',
    type='google.cloud.storage.object.v1.finalized',
    data=CloudEventDataMock(
        bucket='velociraptor-16p1-mock-users-bucket',
        name='9404001v1.pdf',
        metageneration='1',
        timeCreated='2023-05-08T19:28:55.255Z',
        updated='2023-05-08T19:28:55.255Z',
    )
)
