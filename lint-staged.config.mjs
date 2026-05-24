import path from 'node:path';

/** @param {string[]} filenames */
function toRelative(cwd, filenames) {
	return filenames.map((file) => path.relative(cwd, file));
}

/** @param {string[]} filenames */
function clientTasks(filenames) {
	if (filenames.length === 0) return [];

	const cwd = 'client';
	const files = toRelative(cwd, filenames).map((file) => `"${file}"`).join(' ');

	return [
		`cd ${cwd} && bunx prettier --write --ignore-unknown ${files}`,
		`cd ${cwd} && bunx eslint --fix ${files}`
	];
}

/** @param {string[]} filenames */
function serverTasks(filenames) {
	if (filenames.length === 0) return [];

	const cwd = 'server';
	const files = toRelative(cwd, filenames);
	const fileArgs = files.map((file) => `"${file}"`).join(' ');
	const packages = [...new Set(files.map((file) => path.dirname(file)))];
	const lintTargets =
		packages.length > 0
			? packages.map((pkg) => `"./${pkg === '.' ? '...' : `${pkg}/...`}"`).join(' ')
			: '"./..."';

	return [
		`cd ${cwd} && gofmt -w ${fileArgs}`,
		`cd ${cwd} && golangci-lint run --fix ${lintTargets}`
	];
}

/** @type {import('lint-staged').Configuration} */
export default {
	'client/**/*.{js,ts,mjs,cjs,svelte,css,scss,html,json,md,yml,yaml}': clientTasks,
	'server/**/*.go': serverTasks
};
