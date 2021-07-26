import os, struct, zlib, lzma
from pathlib import Path

def pack(target_folder, output_file):
	files = []
	for dirname, dirnames, filenames in os.walk(target_folder):
		for filename in filenames:
			files.append(os.path.join(dirname, filename).replace(f'{target_folder}/', ''))
	
	base_offset = struct.calcsize('>IIIIIIIIIII')
	for file in files:
		base_offset += struct.calcsize('>IIIQQII')
		base_offset += len(file)

	os.chdir(Path.cwd() / target_folder)

	with open(output_file, 'wb') as file:
		file.write(b'\x50\xEC\x12\xBA')
		file.write(struct.pack('>IIIIIIIIIII',
							   5,
							   8,
							   base_offset,
							   len(files),
							   0,
							   0,
							   0,
							   0,
							   3346979248,
							   241478,
							   len(files)))
		file_offset = 0
		for file_ in files:
			content = open(file_, 'rb').read()
			file.write(struct.pack('>IIIQQ',
								   1,
								   len(content),
								   0,
								   0,
								   file_offset))
			
			filename = os.path.basename(file_)
			filepath = file_.replace(filename, '')

			file.write(struct.pack('>I', len(filename)))
			file.write(filename.encode('utf-8'))
			
			file.write(struct.pack('>I', len(filepath)))
			file.write(filepath.encode('utf-8'))

			file.write(struct.pack('>I', zlib.crc32(filename.encode('utf-8'))))
			file.write(struct.pack('>I', 0))

			file_offset += len(content)
		
		for file_ in files:
			file.write(open(file_, 'rb').read())
		
		file.close()

def extract(target_file, output_folder):
	with open(target_file, 'rb') as file:
		assert file.read(4) == b'\x50\xEC\x12\xBA'

		unpackedBytesLength = struct.calcsize('>IIIIIIIIIII')
		unpackedBytes = struct.unpack('>IIIIIIIIIII', file.read(unpackedBytesLength))

		version = unpackedBytes[0]
		base_offset = unpackedBytes[2]
		num_files = unpackedBytes[3]

		chunks = []
		for _ in range(num_files):
			chunk = {}

			unpackedBytesLength = struct.calcsize('>IIIQQ')
			unpackedBytes = struct.unpack('>IIIQQ', file.read(unpackedBytesLength))
			
			chunk['size'] = unpackedBytes[1]
			chunk['compressed_size'] = unpackedBytes[2]
			chunk['offset'] = unpackedBytes[-1]

			if version >= 5:
				length = struct.unpack('>I', file.read(4))[0]
				chunk['name'] = file.read(length).decode('utf-8')

				length = struct.unpack('>I', file.read(4))[0]
				chunk['path'] = file.read(length).decode('utf-8')
			else:
				length = struct.unpack('>I', file.read(4))[0]
				chunk['path'] = file.read(length).decode('utf-8')

				length = struct.unpack('>I', file.read(4))[0]
				chunk['name'] = file.read(length).decode('utf-8')
			
			unpackedBytesLength = struct.calcsize('II')
			unpackedBytes = struct.unpack('>II', file.read(unpackedBytesLength))

			chunks.append(chunk)

		os.chdir(output_folder)

		for chunk in chunks:
			file_path = Path.cwd() / chunk['path']
			file_name = chunk['name']

			file.seek(chunk['offset'] + base_offset)

			file_path.mkdir(parents=True, exist_ok=True)

			with open(file_path / file_name, 'wb') as ff:
				if chunk['compressed_size'] == 0:
					data = file.read(chunk['size'])
				else:
					if version >= 8:
						data = lzma.decompress(file.read(chunk['compressed_size']))
					else:
						data = zlib.decompress(file.read(chunk['compressed_size']))

				ff.write(data)